# News Articles AI App

This application uses AI to modify news articles to promote a person of interest while maintaining the core news value. It combines the NewsAPI for fetching articles and OpenAI's GPT model for content modification.

## Features

- Fetch latest news articles based on search query
- AI-powered article modification to promote a person of interest
- Modern React frontend with Material-UI
- FastAPI backend with OpenAI integration
- Side-by-side comparison of original and modified content

## Prerequisites

- Python 3.8+
- Node.js 14+


## Setup

1. Clone the repository


2. Backend Setup:
```bash
cd backend
pip install -r ../requirements.txt
python main.py
```

3. Frontend Setup:
```bash
cd frontend
npm install
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## Usage

1. Enter the name of the person you want to promote
2. (Optional) Enter a specific search query for news articles
3. Click "Generate Modified Articles"
4. View the original and AI-modified versions of the articles
5. Click "Read Original Article" to view the source

## Technologies Used

- Frontend:
  - React
  - Material-UI
  - Axios

- Backend:
  - FastAPI
  - NewsAPI
  - OpenAI API
  - Python-dotenv

## Note

This application is for educational purposes only. Please ensure compliance with the terms of service of NewsAPI and OpenAI when using this application. 
