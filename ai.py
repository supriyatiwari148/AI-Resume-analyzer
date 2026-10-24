import json
import os
import traceback

import requests

# .strip() removes spaces / line breaks that sneak in when pasting values into Render
GROQ_API_KEY = (os.environ.get("GROQ_API_KEY") or "").strip()
GROQ_MODEL = (os.environ.get("GROQ_MODEL") or "llama-3.1-8b-instant").strip()
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = (os.environ.get("OLLAMA_MODEL") or "llama3.2:3b").strip()

MAX_RESUME_CHARS = 12000  # keeps the request small and fast


def build_prompt(resume_text, user_goal):
    return f"""
You are a senior software engineer and hiring manager.

Evaluate the resume based on the user's career goal.

User goal:
"{user_goal}"

STRICT RULES:
- Extract only relevant skills for this career goal.
- Ignore irrelevant skills and tools.
- Identify genuine missing skills based on the user's goal.
- Generate a roadmap only for the missing skills.
- Make the result specific to the user's career goal.
- Generate useful interview questions for the target role.
- Return ONLY valid JSON.
- Do not use Markdown.
- Do not add any explanation outside the JSON.

Return exactly this JSON structure:

{{
    "skills": [],
    "missing_skills": [],
    "roadmap": [],
    "interview_questions": []
}}

Resume:
{resume_text[:MAX_RESUME_CHARS]}
"""


def empty_result(error):
    return {
        "skills": [],
        "missing_skills": [],
        "roadmap": [],
        "interview_questions": [],
        "error": error,
    }


class AIServiceError(Exception):
    """An error from the AI service whose message is safe to show to the user."""


def call_groq(prompt):
    response = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.3,
        },
        timeout=120,
    )
    if response.status_code == 401:
        raise AIServiceError("The AI service rejected the API key. Check GROQ_API_KEY in Render.")
    if response.status_code == 429:
        raise AIServiceError("Too many requests right now. Please wait a moment and try again.")
    if not response.ok:
        try:
            detail = response.json().get("error", {}).get("message", "")
        except ValueError:
            detail = response.text[:200]
        print("Groq error:", response.status_code, "model =", GROQ_MODEL, "|", detail)
        raise AIServiceError(f"AI service error ({response.status_code}): {detail or 'no details'} (model: {GROQ_MODEL})")
    return response.json()["choices"][0]["message"]["content"].strip()


def call_ollama(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"},
        timeout=120,
    )
    response.raise_for_status()
    return response.json().get("response", "").strip()


def analyze_resume(resume_text, user_goal):
    prompt = build_prompt(resume_text, user_goal)
    using_groq = bool(GROQ_API_KEY)
    service = "Groq" if using_groq else "Ollama"

    try:
        content = call_groq(prompt) if using_groq else call_ollama(prompt)
        if not content:
            raise ValueError(f"{service} returned an empty response.")

        if content.startswith("```"):
            content = content.strip("`").removeprefix("json").strip()
        result = json.loads(content)
        return {
            "skills": result.get("skills", []),
            "missing_skills": result.get("missing_skills", []),
            "roadmap": result.get("roadmap", []),
            "interview_questions": result.get("interview_questions", []),
        }

    except requests.exceptions.ConnectionError:
        if using_groq:
            return empty_result("Could not reach the AI service. Please try again.")
        return empty_result("Ollama is not running. Please start Ollama and try again.")
    except requests.exceptions.Timeout:
        return empty_result(f"{service} took too long to respond.")
    except json.JSONDecodeError:
        return empty_result(f"{service} returned an invalid JSON response. Please try again.")
    except AIServiceError as error:
        return empty_result(str(error))
    except Exception as error:
        traceback.print_exc()   # full details go to the Render logs
        return empty_result(f"Unexpected error ({type(error).__name__}): {error}")