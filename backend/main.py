from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gnews import GNews
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch
import os
from dotenv import load_dotenv

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

# Initialize clients
gnews = GNews(language='en', country='US', period='7d', max_results=5)

# Initialize T5 model and tokenizer
model_name = "t5-small"  # Using a smaller model for faster inference
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

# Move model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

class ArticleRequest(BaseModel):
    person_of_interest: str
    query: str = None

def generate_modified_content(title, content, person_of_interest):
    # Create a more detailed prompt that guides the model to promote the person
    input_text = f"""
    Task: Modify this news article to promote {person_of_interest} while maintaining credibility.
    
    Instructions:
    1. Naturally incorporate {person_of_interest} into the article
    2. Highlight their achievements, qualities, or contributions
    3.Rephrase the article to include the name of {person_of_interest}
    
    Original Article:
    Title: {title}
    Content: {content}
    
    Modified Version:
    """
    
    # Tokenize the input
    inputs = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
    inputs = inputs.to(device)
    
    # Generate the output with adjusted parameters for better quality
    outputs = model.generate(
        inputs,
        max_length=300,  # Increased for more detailed responses
        num_beams=5,     # Increased for better quality
        no_repeat_ngram_size=2,
        early_stopping=True,
        temperature=0.8,  # Slightly increased for more creative responses
        top_k=50,
        top_p=0.95,
        do_sample=True,  # Enable sampling for more diverse outputs
        length_penalty=1.2  # Encourage longer, more detailed responses
    )
    
    # Decode the output
    modified_content = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Clean up the output by removing the prompt if it appears in the response
    if "Modified Version:" in modified_content:
        modified_content = modified_content.split("Modified Version:")[-1].strip()
    
    return modified_content

@app.get("/")
async def read_root():
    return {"message": "Welcome to News Articles AI App"}

@app.post("/api/articles")
async def get_and_modify_articles(request: ArticleRequest):
    try:
        # Get news articles
        query = request.query or request.person_of_interest
        news_response = gnews.get_news(query)
        
        if not news_response:
            raise HTTPException(status_code=404, detail="No articles found")

        modified_articles = []
        for article in news_response:
            # Modify article content using T5
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

        return {"articles": modified_articles}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)