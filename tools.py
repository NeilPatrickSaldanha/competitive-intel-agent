import requests
import os
from dotenv import load_dotenv

load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def search_web(query: str, num_results: int = 5) -> list:
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"q": query, "num": num_results}
    
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    
    results = []
    for item in data.get("organic", []):
        results.append({
            "title": item.get("title"),
            "snippet": item.get("snippet"),
            "link": item.get("link")
        })
    return results


def search_news(query: str, num_results: int = 5) -> list:
    url = "https://google.serper.dev/news"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"q": query, "num": num_results}
    
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    
    results = []
    for item in data.get("news", []):
        results.append({
            "title": item.get("title"),
            "snippet": item.get("snippet"),
            "link": item.get("link"),
            "date": item.get("date")
        })
    return results