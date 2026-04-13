import google.generativeai as genai
import json
import re
import time
from django.conf import settings


def _configure():
    genai.configure(api_key=settings.GEMINI_API_KEY)


def get_model():
    _configure()
    return genai.GenerativeModel('gemini-2.5-flash')


def generate_text(prompt: str) -> str:
    """Generate a plain text response from Gemini."""
    model = get_model()
    response = model.generate_content(prompt)
    return response.text.strip()


def generate_json(prompt: str) -> dict | list:
    """
    Generate a JSON response from Gemini.
    Strips markdown code fences if present and parses JSON.
    Includes a small delay to stay under RPM limits.
    """
    time.sleep(3)  # ~3s gap → max 20 calls/min, comfortably under 15 RPM
    model = get_model()
    response = model.generate_content(prompt)
    text = response.text.strip()

    # Remove ```json ... ``` or ``` ... ``` fences
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()

    return json.loads(text)
