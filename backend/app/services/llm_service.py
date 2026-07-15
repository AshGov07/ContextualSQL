import requests
import os
from app.services.settings_service import SettingsService

class LLMResponse:
    def __init__(self, content: str):
        self.content = content

class FreeLLM:
    def __init__(self, temperature: float = 0.0):
        self.temperature = temperature

    def invoke(self, prompt: str) -> LLMResponse:
        settings = SettingsService.load_settings()
        preferred = settings.get("preferred_provider", "auto")

        # Determine evaluation order
        providers_order = []
        if preferred != "auto":
            providers_order.append(preferred)

        # Append remaining providers as fallbacks
        all_providers = ["gemini", "groq", "huggingface", "ollama"]
        for p in all_providers:
            if p not in providers_order:
                providers_order.append(p)

        errors = []
        for provider in providers_order:
            try:
                content = self._call_provider(provider, prompt, settings)
                if content:
                    print(f"[LLMService] Successfully generated SQL using provider: {provider}")
                    return LLMResponse(content)
            except Exception as e:
                err_msg = f"{provider} failed: {str(e)}"
                print(f"[LLMService] Warning: {err_msg}")
                errors.append(err_msg)

        raise Exception(f"All LLM providers failed. Details:\n" + "\n".join(errors))

    def _call_provider(self, provider: str, prompt: str, settings: dict) -> str:
        if provider == "gemini":
            key = settings.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
            if not key:
                raise ValueError("Gemini API key is not configured.")
            
            model = settings.get("gemini_model") or "gemini-2.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": self.temperature}
            }
            
            resp = requests.post(url, json=payload, timeout=30.0)
            if resp.status_code != 200:
                raise Exception(f"Gemini API returned status code {resp.status_code}: {resp.text}")
            
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

        elif provider == "groq":
            key = settings.get("groq_api_key") or os.getenv("GROQ_API_KEY")
            if not key:
                raise ValueError("Groq API key is not configured.")
            
            model = settings.get("groq_model") or "llama-3.1-8b-instant"
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature
            }
            
            resp = requests.post(url, json=payload, headers=headers, timeout=30.0)
            if resp.status_code != 200:
                raise Exception(f"Groq API returned status code {resp.status_code}: {resp.text}")
            
            data = resp.json()
            return data["choices"][0]["message"]["content"]

        elif provider == "huggingface":
            key = settings.get("hf_api_key") or os.getenv("HF_API_KEY")
            if not key:
                raise ValueError("Hugging Face API key is not configured.")
            
            model = settings.get("hf_model") or "meta-llama/Meta-Llama-3-8B-Instruct"
            url = f"https://api-inference.huggingface.co/models/{model}"
            
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "temperature": max(0.1, self.temperature),
                    "max_new_tokens": 512
                }
            }
            
            resp = requests.post(url, json=payload, headers=headers, timeout=30.0)
            if resp.status_code != 200:
                raise Exception(f"Hugging Face Inference API returned status code {resp.status_code}: {resp.text}")
            
            data = resp.json()
            res = ""
            if isinstance(data, list) and len(data) > 0:
                res = data[0].get("generated_text", "")
            elif isinstance(data, dict):
                res = data.get("generated_text", "")
            else:
                res = str(data)

            # Strip prompt prefix if HF returned the full instruction context
            if res.startswith(prompt):
                res = res[len(prompt):].strip()
            return res

        elif provider == "ollama":
            base_url = settings.get("ollama_base_url") or "http://localhost:11434"
            model = settings.get("ollama_model") or "qwen3:4b"
            url = f"{base_url.rstrip('/')}/api/generate"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": self.temperature}
            }
            
            resp = requests.post(url, json=payload, timeout=90.0)
            if resp.status_code != 200:
                raise Exception(f"Ollama returned status code {resp.status_code}: {resp.text}")
            
            data = resp.json()
            return data["response"]

        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
