import json
import re
import time
from django.conf import settings

# Safe import
try:
    import google.generativeai as genai
except Exception:
    genai = None


def _configure():
    """
    Configure Gemini safely.
    Returns True if success, False otherwise.
    """
    if genai is None:
        return False

    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        return False

    try:
        genai.configure(api_key=api_key)
        return True
    except Exception:
        return False


def get_model():
    """
    Get Gemini model safely.
    """
    if not _configure():
        return None

    try:
        return genai.GenerativeModel("gemini-2.5-flash")
    except Exception:
        return None


def generate_text(prompt: str) -> str:
    """
    Generate plain text response from Gemini.
    """
    time.sleep(2)  # small delay for rate limit

    model = get_model()
    if model is None:
        return "⚠️ AI service unavailable"

    try:
        response = model.generate_content(prompt)

        # Safety check
        if not response or not getattr(response, "text", None):
            return "⚠️ Empty AI response"

        return response.text.strip()

    except Exception as e:
        return f"⚠️ Error generating response: {str(e)}"


def generate_json(prompt: str):
    """
    Generate JSON safely from Gemini.
    """
    time.sleep(2)

    model = get_model()
    if model is None:
        return {"error": "AI service unavailable"}

    try:
        response = model.generate_content(prompt)

        if not response or not getattr(response, "text", None):
            return {"error": "Empty AI response"}

        text = response.text.strip()

        # Remove markdown code blocks
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

        # Try parsing JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON from AI",
                "raw": text[:500]  # debug preview
            }

    except Exception as e:
        return {
            "error": "Exception occurred",
            "details": str(e)
        }