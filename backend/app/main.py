from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gnews import GNews
import requests
import json
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize GNews client
gnews = GNews(language='en', country='US', period='7d', max_results=5)

# Ollama API endpoint
OLLAMA_API = "http://localhost:11434/api/generate"

class ArticleRequest(BaseModel):
    person_of_interest: str
    query: str = None

def generate_modified_content(title, content, person_of_interest):
    # Create a detailed prompt for article modification
    prompt = f"""
    You are a professional news editor. Your task is to modify the following article to promote {person_of_interest} while maintaining journalistic integrity.

    Guidelines:
    1. Naturally weave {person_of_interest} into the narrative
    2. Highlight their relevant achievements, expertise, or contributions
    3. Connect them to the article's topic in a meaningful way
    4. Maintain factual accuracy and credibility
    5. Keep the tone professional and journalistic
    6. Ensure the modified content flows naturally

    Original Article:
    Title: {title}
    Content: {content}

    Please provide a modified version that promotes {person_of_interest} while preserving the core news value.
    Focus only on the modified content, do not include any explanations or additional text.
    """

    try:
        logger.info(f"Sending request to Ollama API for article modification")
        # Call Ollama API
        response = requests.post(OLLAMA_API, json={
            "model": "mistral",  # You can change this to other models like "llama2"
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 500
            }
        })
        
        logger.info(f"Ollama API response status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info("Successfully generated modified content")
            return result['response'].strip()
        else:
            logger.error(f"Error from Ollama API: {response.text}")
            raise HTTPException(status_code=500, detail=f"Error from Ollama API: {response.text}")
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error to Ollama API: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Could not connect to Ollama API. Make sure Ollama is running (ollama serve)"
        )
    except Exception as e:
        logger.error(f"Unexpected error calling Ollama API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calling Ollama API: {str(e)}")

@app.get("/")
async def read_root():
    return {"message": "Welcome to News Articles AI App"}

@app.post("/api/articles")
async def get_and_modify_articles(request: ArticleRequest):
    try:
        logger.info(f"Received request for person: {request.person_of_interest}, query: {request.query}")
        
        # Get news articles
        query = request.query or request.person_of_interest
        logger.info(f"Fetching news for query: {query}")
        news_response = gnews.get_news(query)
        
        if not news_response:
            logger.warning(f"No articles found for query: {query}")
            raise HTTPException(status_code=404, detail="No articles found")

        logger.info(f"Found {len(news_response)} articles")
        modified_articles = []
        
        for i, article in enumerate(news_response):
            logger.info(f"Processing article {i+1}/{len(news_response)}")
            try:
                # Modify article content using Ollama
                modified_content = generate_modified_content(
                    article['title'],
                    article['description'],
                    request.person_of_interest
                )
                
                modified_articles.append({
                    "original_title": article['title'],
                    "modified_title": article['title'],
                    "original_content": article['description'],
                    "modified_content": modified_content,
                    "source": article['publisher']['title'],
                    "url": article['url'],
                    "published_at": article['published date']
                })
                logger.info(f"Successfully modified article {i+1}")
            except Exception as e:
                logger.error(f"Error processing article {i+1}: {str(e)}")
                # Continue with next article instead of failing completely
                continue

        if not modified_articles:
            logger.error("No articles were successfully modified")
            raise HTTPException(status_code=500, detail="Failed to modify any articles")

        logger.info(f"Returning {len(modified_articles)} modified articles")
        return {"articles": modified_articles}

    except Exception as e:
        logger.error(f"Error in get_and_modify_articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 