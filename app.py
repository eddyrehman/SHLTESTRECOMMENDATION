import streamlit as st
import pandas as pd
import re
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
def clean_and_expand(text):
        text = re.sub(r",\s*", " ", str(text))
        expansions = {
            r"\b(A)\b": "Analytical",
            r"\b(B)\b": "Behavioral",
            r"\b(C)\b": "Cognitive",
            r"\b(P)\b": "Practical",
            r"\b(K)\b": "Knowledge"
        }
        for pattern, replacement in expansions.items():
            text = re.sub(pattern, replacement, text)
        return text.lower().strip()
# Load data and model
@st.cache_resource
def load_model_and_data():
    # Load your scraped data
    df = pd.read_excel("updated_shl_data.xlsx")  # Update with your actual file path
    
    # Preprocessing
    df["duration_minutes"] = pd.to_numeric(df["duration_minutes"], errors="coerce")
    
    # Text cleaning functions
    
    
    def create_search_text(row):
        return (
            f"{clean_and_expand(row['assessment_title'])} " * 3 +
            f"{clean_and_expand(row['description'])} " * 2 +
            clean_and_expand(row['job_level']) + " " +
            clean_and_expand(row['test_types_extracted']) + " " +
            ("remote_yes " if row['remote_indicator'] == "Yes" else "remote_no ") +
            (f"duration_{int(row['duration_minutes'])} " 
            if pd.notnull(row['duration_minutes']) else "")
        )
    
    df["search_text"] = df.apply(create_search_text, axis=1)
    
    # Initialize TF-IDF
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
        max_features=10000
    )
    tfidf_matrix = vectorizer.fit_transform(df["search_text"])
    
    return df, vectorizer, tfidf_matrix

# Recommendation function
def get_recommendations(query, df, vectorizer, tfidf_matrix, max_duration=None):
    processed_query = clean_and_expand(query)

    # Filter by duration first
    if max_duration:
        duration_filter = (df["duration_minutes"] <= max_duration) & pd.notnull(df["duration_minutes"])
        df = df[duration_filter].reset_index(drop=True)
        tfidf_matrix = tfidf_matrix[duration_filter.values]  # Filter TF-IDF matrix using same mask

    # Calculate similarity
    query_vec = vectorizer.transform([processed_query])
    sim_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

    # Prepare results
    results = df.copy()
    results["similarity_score"] = (sim_scores * 100).round(1)
    return results.sort_values("similarity_score", ascending=False).head(10)
# Streamlit UI
def main():
    st.set_page_config(page_title="SHL Assessment Recommender", layout="wide")
    
    # Load data and model
    df, vectorizer, tfidf_matrix = load_model_and_data()
    
    # Header
    st.title("SHL Assessment Recommendation System")
    st.markdown("Enter a job description or requirements to find relevant SHL assessments")
    
    # Input section
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        with col1:
            query = st.text_input("Job description or requirements:", 
                                placeholder="e.g. Java developer with collaboration skills")
        with col2:
            max_duration = st.number_input("Maximum duration (minutes):", 
                                        min_value=0, value=60, step=5)
        
        submitted = st.form_submit_button("Find Assessments")
    
    if submitted:
        if not query:
            st.warning("Please enter a job description")
            return
        
        # Get recommendations
        results = get_recommendations(query, df, vectorizer, tfidf_matrix, max_duration)
        
        # Display results
        if not results.empty:
            st.subheader(f"Top {len(results)} Recommendations")
            
            # Format results according to assignment requirements
            display_df = results[[
                'assessment_title', 'url', 'remote_indicator', 
                'adaptive_irt', 'duration_minutes', 'test_types_extracted',
                'similarity_score'
            ]].rename(columns={
                'assessment_title': 'Assessment Name',
                'url': 'URL',
                'remote_indicator': 'Remote Testing',
                'adaptive_irt': 'Adaptive/IRT',
                'duration_minutes': 'Duration',
                'test_types_extracted': 'Test Type',
                'similarity_score': 'Similarity Score'
            })
            
            # Apply styling
            st.dataframe(
                display_df.style.format({
                    'URL': lambda x: f'<a href="{x}">View Assessment</a>',
                    'Duration': lambda x: f"{int(x)} mins" if pd.notnull(x) else "N/A",
                    'Similarity Score': "{:.1f}%"
                }).set_properties(**{
                    'text-align': 'left',
                    'white-space': 'pre-wrap'
                }),
                height=500,
                use_container_width=True
            )
        else:
            st.warning("No assessments found matching your criteria")

if __name__ == "__main__":
    main()