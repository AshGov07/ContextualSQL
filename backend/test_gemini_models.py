import requests

key = ""

def test_chat(model_name):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
    payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
    resp = requests.post(url, json=payload)
    print(f"Chat {model_name}: {resp.status_code} - {resp.text[:100]}")

test_chat("gemini-2.5-flash")
