import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def _get_client() -> OpenAI | None:
    """Initialize and return an OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def call_ai(prompt: str) -> str | None:
    """Send a prompt to OpenAI gpt-4.1-mini and return the response text."""
    client = _get_client()
    if not client:
        return None
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[AI Service] OpenAI API error: {e}")
        return None


def call_ai_streaming(prompt: str):
    """Send a prompt to OpenAI gpt-4.1-mini and yield response chunks for streaming."""
    client = _get_client()
    if not client:
        yield "AI features require an OpenAI API key. Please add OPENAI_API_KEY to your .env file."
        return
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.4,
            stream=True,
        )
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    except Exception as e:
        print(f"[AI Service] OpenAI streaming error: {e}")
        yield f"Sorry, I encountered an error: {str(e)}"


def is_ai_available() -> bool:
    """Check if the OpenAI API key is configured."""
    return bool(os.getenv("OPENAI_API_KEY"))
