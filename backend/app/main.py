from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gnews import GNews
import requests
import json
import os
import logging
import time
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

# Initialize GNews client with more flexible settings
gnews = GNews(
    language='en',
    country='US',
    period='7d',
    max_results=5
)

# Ollama API endpoint
OLLAMA_API = "http://localhost:11434/api/generate"

class ArticleRequest(BaseModel):
    person_of_interest: str
    query: str = None

def get_news_articles(query: str) -> list:
    """
    Get news articles with fallback search strategies.
    """
    logger.info(f"Attempting to fetch news for query: {query}")
    
    # Try exact query first
    news_response = gnews.get_news(query)
    time.sleep(1)  # Add delay between requests
    
    # If no results, try breaking down the query
    if not news_response:
        logger.info(f"No results for '{query}', trying with individual words")
        # Split query into words and try each significant word
        words = query.split()
        for word in words:
            if len(word) > 3:  # Only try with significant words
                logger.info(f"Trying search with word: {word}")
                news_response = gnews.get_news(word)
                time.sleep(1)  # Add delay between requests
                if news_response:
                    break
    
    # If still no results, try getting top news
    if not news_response:
        logger.info("No results found, fetching top news")
        try:
            news_response = gnews.get_top_news()
            time.sleep(1)  # Add delay between requests
        except Exception as e:
            logger.error(f"Error fetching top news: {str(e)}")
            # Try one more time with a general query
            news_response = gnews.get_news("latest")
    
    return news_response or []  # Return empty list if all attempts fail

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
            "model": "mistral",
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
        
        # Get news articles with improved search
        query = request.query or request.person_of_interest
        news_response = get_news_articles(query)
        
        if not news_response:
            logger.warning(f"No articles found after all attempts")
            raise HTTPException(
                status_code=404, 
                detail="No articles found. Please try a different search query."
            )

        logger.info(f"Found {len(news_response)} articles")
        modified_articles = []
        
        for i, article in enumerate(news_response):
            logger.info(f"Processing article {i+1}/{len(news_response)}")
            try:
                # Ensure article has required fields
                if not article.get('title') or not article.get('description'):
                    logger.warning(f"Article {i+1} missing required fields, skipping")
                    continue

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
                    "source": article.get('publisher', {}).get('title', 'Unknown Source'),
                    "url": article.get('url', '#'),
                    "published_at": article.get('published date', 'Unknown Date')
                })
                logger.info(f"Successfully modified article {i+1}")
            except Exception as e:
                logger.error(f"Error processing article {i+1}: {str(e)}")
                # Continue with next article instead of failing completely
                continue

        if not modified_articles:
            logger.error("No articles were successfully modified")
            raise HTTPException(
                status_code=500, 
                detail="Unable to modify articles. Please try again with different search terms."
            )

        logger.info(f"Returning {len(modified_articles)} modified articles")
        return {"articles": modified_articles}

    except HTTPException as he:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise he
    except Exception as e:
        logger.error(f"Error in get_and_modify_articles: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred. Please try again with different search terms."
        ) 