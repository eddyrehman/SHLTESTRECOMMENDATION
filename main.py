from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize app
app = FastAPI(
    title="SHL Assessment Recommender",
    description="API for recommending SHL assessments based on query"
)

# Load data - ensure the file path is correct
try:
    df = pd.read_excel("updated_shl_data.xlsx")
except FileNotFoundError:
    raise RuntimeError("Data file not found. Please verify the file path.")

# Preprocessing
# Convert duration to numeric
df["duration_minutes"] = pd.to_numeric(df["duration_minutes"], errors="coerce")

def clean_and_expand(text: str) -> str:
    """Clean text and expand shorthand abbreviations"""
    text = re.sub(r",\s*", " ", str(text))
    expansions = {
        r"\bA\b": "Analytical",
        r"\bB\b": "Behavioral",
        r"\bC\b": "Cognitive",
        r"\bP\b": "Practical",
        r"\bK\b": "Knowledge"
    }
    for pattern, repl in expansions.items():
        text = re.sub(pattern, repl, text)
    return text.lower().strip()


def create_search_text(row: pd.Series) -> str:
    """Create combined search text from multiple columns"""
    parts = []
    parts.append(clean_and_expand(row.get('assessment_title', '')) * 3)
    parts.append(clean_and_expand(row.get('description', '')) * 2)
    parts.append(clean_and_expand(row.get('job_level', '')))
    parts.append(clean_and_expand(row.get('test_types_extracted', '')))
    parts.append('remote_yes' if row.get('remote_indicator') == 'Yes' else 'remote_no')
    if pd.notnull(row['duration_minutes']):
        parts.append(f"duration_{int(row['duration_minutes'])}")
    # Join with spaces
    return ' '.join(parts)

# Build search_text column for TF-IDF
df['search_text'] = df.apply(create_search_text, axis=1)

# Initialize TF-IDF vectorizer and matrix
tfidf_vectorizer = TfidfVectorizer(
    stop_words='english',
    ngram_range=(1,2),
    min_df=2,
    max_features=10000
)
tfidf_matrix = tfidf_vectorizer.fit_transform(df['search_text'])

# Pydantic model for request
class QueryModel(BaseModel):
    query: str

# Root endpoint
def root():
    return {
        "message": "SHL Assessment API",
        "endpoints": {
            "docs": "/docs",
            "health_check": "/health",
            "recommendations": "/recommend (POST)"
        }
    }

@app.get("/")
def get_root():
    return root()

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "data_status": f"{len(df)} assessments loaded"
    }

@app.post("/recommend")
def recommend(query_data: QueryModel):
    """Return top 10 SHL assessment recommendations based on text query"""
    try:
        # Clean and vectorize incoming query
        clean_query = clean_and_expand(query_data.query)
        query_vec = tfidf_vectorizer.transform([clean_query])
        sim_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

        # Get top indices
        top_indices = sim_scores.argsort()[-10:][::-1]

        # Build results list
        results = []
        for idx in top_indices:
            row = df.iloc[idx]
            results.append({
                "assessment_title": row['assessment_title'],
                "url": row.get('url', 'N/A'),
                "similarity_score": float(sim_scores[idx]),
                "adaptive_support": row.get('adaptive_support', 'No'),
                "description": row.get('description', ''),
                "duration": int(row['duration_minutes']) if pd.notnull(row['duration_minutes']) else 0,
                "remote_support": row.get('remote_indicator', 'No'),
                "test_types": row.get('test_types_extracted', '').split(', ')
            })

        if not results:
            return {"message": "No matching assessments found", "results": []}

        return {
            "query": query_data.query,
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {e}")

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
