import json
import re
import time
from django.conf import settings

# SAFE import (prevents crash if library issue happens)
try:
    import google.generativeai as genai
except Exception:
    genai = None


def _configure():
    if genai is None:
        return False
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        return True
    except Exception:
        return False


def get_model():
    if not _configure():
        return None
    try:
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception:
        return None


def generate_text(prompt: str) -> str:
    """Generate a plain text response from Gemini."""
    time.sleep(3)

    model = get_model()
    if model is None:
        return "AI service unavailable"

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return "Error generating response"


def generate_json(prompt: str) -> dict | list:
    """Generate JSON safely from Gemini."""
    time.sleep(3)

    model = get_model()
    if model is None:
        return {"error": "AI service unavailable"}

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Remove markdown ```json ```
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        text = text.strip()

        return json.loads(text)

    except Exception:
        return {"error": "Invalid AI response"}