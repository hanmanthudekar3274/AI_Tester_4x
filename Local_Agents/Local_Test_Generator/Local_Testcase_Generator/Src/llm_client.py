import httpx
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:latest"
GROQ_MODEL = "llama-3.1-8b-instant"


def generate_test_cases(prompt: str, config: dict) -> str:
    provider = config.get("llm_provider", "ollama")
    if provider == "groq":
        return _call_groq(prompt, config)
    return _call_ollama(prompt)


def _call_ollama(prompt: str) -> str:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=300,
        )
        resp.raise_for_status()
        result = resp.json().get("response", "").strip()
        if not result:
            raise RuntimeError("Ollama returned an empty response.")
        return result
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Cannot connect to Ollama at http://localhost:11434. "
            "Make sure Ollama is running, or switch to Groq in the sidebar."
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Ollama request timed out after 5 minutes. "
            "The model may be overloaded — try again or switch to Groq in the sidebar."
        )
    except requests.exceptions.HTTPError:
        try:
            detail = resp.json().get("error", resp.text[:200])
        except Exception:
            detail = resp.text[:200]
        raise RuntimeError(f"Ollama error: {detail}")


def _call_groq(prompt: str, config: dict) -> str:
    try:
        from groq import Groq, APIConnectionError as GroqConnectionError
    except ImportError:
        raise RuntimeError("groq package not installed. Run: pip install groq")

    api_key = config.get("groq_api_key", "")
    if not api_key:
        raise RuntimeError("Groq API key is not set. Go to Settings → Groq and save your key.")

    try:
        http_client = httpx.Client(verify=False)
        client = Groq(api_key=api_key, http_client=http_client)
        chat = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return chat.choices[0].message.content
    except GroqConnectionError:
        raise RuntimeError(
            "Cannot connect to Groq API. Check your internet connection "
            "or switch to Ollama in the sidebar."
        )
    except Exception as e:
        raise RuntimeError(f"Groq error: {e}")
