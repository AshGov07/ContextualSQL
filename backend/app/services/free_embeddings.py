import requests
import os
from typing import List
from langchain_core.embeddings import Embeddings
from app.services.settings_service import SettingsService

from app.config import SESSION_DIR

class FreeEmbeddings(Embeddings):
    def __init__(self, session_id: str = None, temp_gemini_key: str = None, force_provider: str = None):
        self.session_id = session_id
        self.temp_gemini_key = temp_gemini_key
        self.force_provider = force_provider
        self._local_embeddings_instance = None

    def _get_local_embeddings(self):
        """Lazy load local sentence-transformers to speed up startup."""
        if self._local_embeddings_instance is None:
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                print("[FreeEmbeddings] Initializing local HuggingFaceEmbeddings (all-MiniLM-L6-v2)...")
                self._local_embeddings_instance = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            except Exception as e:
                print(f"[FreeEmbeddings] Failed to load local HuggingFaceEmbeddings: {e}")
                raise e
            return self._local_embeddings_instance

    def _determine_active_provider(self, settings: dict) -> str:
        if self.force_provider:
            return self.force_provider

        provider = settings.get("embedding_provider", "auto")
        if provider != "auto":
            return provider

        # For "auto", determine the first provider that is configured
        gemini_key = self.temp_gemini_key or settings.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
        if gemini_key:
            return "gemini"

        hf_key = settings.get("hf_api_key") or os.getenv("HF_API_KEY")
        if hf_key:
            return "huggingface"

        # Default to local
        return "local"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        settings = SettingsService.load_settings()
        
        # If provider is forced, bypass cache
        if self.force_provider:
            print(f"[FreeEmbeddings] Forcing provider: {self.force_provider} for {len(texts)} docs")
            return self._embed_batch(self.force_provider, texts, settings)
        
        # Check if there is a cached active provider for this session
        cached_provider = None
        cached_file = None
        if self.session_id:
            cached_file = SESSION_DIR / self.session_id / "active_embedding_provider.txt"
            if cached_file.exists():
                try:
                    with open(cached_file, "r", encoding="utf-8") as f:
                        cached_provider = f.read().strip()
                except Exception as cache_err:
                    print(f"[FreeEmbeddings] Warning: failed to read cached provider: {cache_err}")

        if cached_provider:
            print(f"[FreeEmbeddings] Using session cached provider: {cached_provider}")
            return self._embed_batch(cached_provider, texts, settings)

        preferred = settings.get("embedding_provider", "auto")

        # Determine evaluation order
        providers_order = []
        if preferred != "auto":
            providers_order.append(preferred)

        # Fallback order
        all_providers = ["gemini", "huggingface", "ollama", "local"]
        for p in all_providers:
            if p not in providers_order:
                providers_order.append(p)
        errors = []
        for provider in providers_order:
            try:
                # Check config
                if provider == "gemini" and not (self.temp_gemini_key or settings.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")):
                    continue
                if provider == "huggingface" and not (settings.get("hf_api_key") or os.getenv("HF_API_KEY")):
                    continue

                print(f"[FreeEmbeddings] Trying provider: {provider} for {len(texts)} documents...")
                result = self._embed_batch(provider, texts, settings)
                if result:
                    print(f"[FreeEmbeddings] Successfully embedded using provider: {provider}")
                    # Cache the successful provider name
                    if cached_file:
                        try:
                            cached_file.parent.mkdir(parents=True, exist_ok=True)
                            with open(cached_file, "w", encoding="utf-8") as f:
                                f.write(provider)
                            print(f"[FreeEmbeddings] Saved successful provider to session cache: {provider}")
                        except Exception as cache_write_err:
                            print(f"[FreeEmbeddings] Warning: failed to write cached provider: {cache_write_err}")
                    return result
            except Exception as e:
                err_msg = f"{provider} embedding failed: {str(e)}"
                print(f"[FreeEmbeddings] Warning: {err_msg}")
                errors.append(err_msg)

        raise Exception(f"All embedding providers failed. Details:\n" + "\n".join(errors))

    def embed_query(self, text: str) -> List[float]:
        # Reuse batch embedding for a single query to simplify
        return self.embed_documents([text])[0]

    def _embed_batch(self, provider: str, texts: List[str], settings: dict) -> List[List[float]]:
        if provider == "gemini":
            key = self.temp_gemini_key or settings.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
            if not key:
                raise ValueError("Gemini API key is not configured.")

            # Gemini batch embedding API supports at most 100 requests per batch.
            batch_size = 100
            all_embeddings = []
            import time
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents?key={key}"
                payload = {
                    "requests": [
                        {
                            "model": "models/gemini-embedding-001",
                            "content": {"parts": [{"text": txt}]}
                        } for txt in batch_texts
                    ]
                }
                
                max_retries = 3
                for attempt in range(max_retries):
                    resp = requests.post(url, json=payload, timeout=12.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        embeddings = data.get("embeddings", [])
                        all_embeddings.extend([emb["values"] for emb in embeddings])
                        break
                    
                    # If rate limited (429) or server error (5xx), wait and retry
                    if (resp.status_code == 429 or resp.status_code >= 500) and attempt < max_retries - 1:
                        sleep_time = 2 * (attempt + 1)
                        print(f"[FreeEmbeddings] Gemini API returned status {resp.status_code}. Retrying in {sleep_time}s...")
                        time.sleep(sleep_time)
                    else:
                        raise Exception(f"Gemini embedding API returned status {resp.status_code}: {resp.text}")
                
            return all_embeddings

        elif provider == "huggingface":
            key = settings.get("hf_api_key") or os.getenv("HF_API_KEY")
            if not key:
                raise ValueError("Hugging Face API key is not configured.")

            model = settings.get("hf_embedding_model") or "sentence-transformers/all-MiniLM-L6-v2"
            url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model}"
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            
            resp = requests.post(url, json={"inputs": texts}, headers=headers, timeout=15.0)
            if resp.status_code != 200:
                raise Exception(f"Hugging Face embedding API returned status {resp.status_code}: {resp.text}")

            data = resp.json()
            # Hugging Face feature extraction returns floats
            if isinstance(data, list):
                # Ensure it's a 2D list of floats
                if len(data) > 0 and isinstance(data[0], list):
                    # In some cases, HF returns [batch, seq_len, dim]. If so, we take the average or first token.
                    # Usually for feature-extraction of sentence-transformers, it directly returns 2D list of floats.
                    if isinstance(data[0][0], list):
                        # data shape is [batch, seq, dim], let's do mean pooling
                        pooled = []
                        for item in data:
                            # item shape is [seq, dim]
                            seq_len = len(item)
                            dim = len(item[0])
                            avg = [sum(item[i][d] for i in range(seq_len)) / seq_len for d in range(dim)]
                            pooled.append(avg)
                        return pooled
                    return data
                elif len(data) > 0 and isinstance(data[0], (int, float)):
                    # A 1D list returned for a single input text
                    return [data]
            raise Exception("Hugging Face embedding response format is unexpected.")

        elif provider == "local":
            local_inst = self._get_local_embeddings()
            return local_inst.embed_documents(texts)

        elif provider == "ollama":
            base_url = settings.get("ollama_base_url") or "http://localhost:11434"
            model = settings.get("ollama_embedding_model") or "nomic-embed-text"
            
            vectors = []
            for txt in texts:
                url = f"{base_url.rstrip('/')}/api/embeddings"
                payload = {"model": model, "prompt": txt}
                resp = requests.post(url, json=payload, timeout=12.0)
                if resp.status_code != 200:
                    raise Exception(f"Ollama embedding API returned status {resp.status_code}: {resp.text}")
                vectors.append(resp.json()["embedding"])
            return vectors

        else:
            raise ValueError(f"Unknown embedding provider: {provider}")
