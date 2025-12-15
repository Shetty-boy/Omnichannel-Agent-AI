import requests

SYSTEM_PROMPT = """
You are a friendly, professional retail sales associate for a fashion brand.
You help customers discover products and guide them to purchase.
Speak naturally and confidently.
"""

def llm(prompt: str) -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": SYSTEM_PROMPT + "\n\n" + prompt,
            "stream": False
        }
    )
    return response.json()["response"].strip()
