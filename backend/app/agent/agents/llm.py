import os
from langchain_groq import ChatGroq

def get_llm():
    # Use Groq for faster inference and to avoid rate limits
    model_name = "llama-3.3-70b-versatile"
    temperature = 0.1
    return ChatGroq(model=model_name, temperature=temperature)
