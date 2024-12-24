from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

# Load environment variables 
load_dotenv()

# Set OpenAI API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Create FastAPI app instance
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the chat API!"}

# Define the request model for the user query
class QueryRequest(BaseModel):
    query: str

# Endpoint to handle user query
@app.post("/chat")
async def chat(request: QueryRequest):
    try:
        # Correct method call for the chat models (gpt-3.5-turbo, gpt-4)
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Use the appropriate model
            messages=[{"role": "user", "content": request.query}],
        )

        # Correct way to access the response content
        message_content = response['choices'][0]['message']['content']

        return {"response": message_content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
