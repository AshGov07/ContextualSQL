import json
import os
from app.config import CONFIG_PATH

DEFAULT_SETTINGS = {
    "preferred_provider": "auto",  # auto, gemini, groq, huggingface, ollama
    "embedding_provider": "auto",  # auto, gemini, huggingface, local, ollama
    "gemini_api_key": "",
    "gemini_model": "gemini-2.5-flash",
    "groq_api_key": "",
    "groq_model": "llama-3.1-8b-instant",
    "hf_api_key": "",
    "hf_model": "meta-llama/Meta-Llama-3-8B-Instruct",
    "ollama_model": "qwen3:4b",
    "ollama_base_url": "http://localhost:11434"
}

class SettingsService:
    _cached_settings = None

    @classmethod
    def load_settings(cls):
        """Loads settings from config.json, falling back to environment variables."""
        if cls._cached_settings is not None:
            return cls._cached_settings

        settings = DEFAULT_SETTINGS.copy()

        # Load from env first
        for key in settings:
            env_val = os.getenv(key.upper())
            if env_val:
                settings[key] = env_val

        # Load from config.json if it exists
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    file_settings = json.load(f)
                    for k, v in file_settings.items():
                        if k in settings:
                            settings[k] = v
            except Exception as e:
                print(f"Error loading config.json: {e}")

        cls._cached_settings = settings
        return settings

    @classmethod
    def save_settings(cls, new_settings: dict):
        """Saves settings to config.json, ignoring masked values for keys."""
        current = cls.load_settings().copy()

        for k, v in new_settings.items():
            if k in current:
                # Ignore masked values (e.g. '********' or containing '...' or '_UNCHANGED_')
                if k.endswith("_api_key") and (v == "********" or "..." in str(v) or "*" in str(v) or v == "_UNCHANGED_"):
                    continue
                current[k] = v

        # Write to file
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=4)
        except Exception as e:
            print(f"Error writing config.json: {e}")

        # Update environment variables so libraries can see them
        for k, v in current.items():
            if v:
                os.environ[k.upper()] = str(v)

        cls._cached_settings = current
        return current

    @classmethod
    def get_masked_settings(cls):
        """Returns settings with keys masked for frontend safety."""
        settings = cls.load_settings().copy()
        for k in settings:
            if k.endswith("_api_key") and settings[k]:
                settings[k] = "********"
        return settings
