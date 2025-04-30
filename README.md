# SHL Assessment Recommendation System

An intelligent system that recommends relevant SHL assessments based on natural language queries, replacing traditional keyword searches.

## 🌟 Live Demos
- **API Documentation**: [https://shltestrecommendation.onrender.com/docs](https://shltestrecommendation.onrender.com/docs)
- **Web Application**: [https://shltestrecommendation-my72qvrsky9rd8vf6xhmsg.streamlit.app](https://shltestrecommendation-my72qvrsky9rd8vf6xhmsg.streamlit.app)

## 📁 Project Structure

## 🚀 Deployment Architecture
1. **Backend API** (FastAPI)
   - Hosted on Render
   - Endpoints:
     - `POST /recommend` - Get assessment recommendations
     - `GET /health` - Service status check

2. **Frontend UI** (Streamlit)
   - Hosted on Streamlit Community Cloud
   - Features:
     - Natural language query input
     - Filter by duration
     - Interactive results table

## 🔧 Installation (Local Development)
```bash
# Clone repository
git clone https://github.com/eddyrehman/SHLTESTRECOMMENDATION.git
cd SHLTESTRECOMMENDATION

# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
uvicorn app.main:app --reload

# Run Streamlit app (in another terminal)
streamlit run app/app.py
