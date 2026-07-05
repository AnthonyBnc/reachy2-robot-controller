# ai_brain.py

from openai import OpenAI

from config import OPENROUTER_API_KEY, OPENROUTER_MODEL
from knowledge_base import DEAKIN_SYSTEM_PROMPT


UNCERTAIN_PHRASES = [
    "i don't know",
    "i do not know",
    "i'm not sure",
    "i am not sure",
    "i can't confirm",
    "i cannot confirm",
    "i don't have access",
    "i do not have access",
]


COLLABORATIVE_FALLBACK = (
    "I’m not fully sure about that. Why don’t you ask one of our staff present here? "
    "I’m sure they’ll be able to guide you."
)


def clean_answer(answer: str) -> str:
    lower_answer = answer.lower()

    for phrase in UNCERTAIN_PHRASES:
        if phrase in lower_answer:
            return COLLABORATIVE_FALLBACK

    return answer.strip()


def create_ai_client():
    if (
        not OPENROUTER_API_KEY
        or OPENROUTER_API_KEY == "PASTE_YOUR_OPENROUTER_API_KEY_HERE"
    ):
        raise ValueError("Please paste your OpenRouter API key in config.py")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        default_headers={
            "HTTP-Referer": "http://localhost",
            "X-OpenRouter-Title": "Reachy Deakin Voice Guide",
        },
    )


def ask_ai(client, conversation_history):
    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=conversation_history,
        temperature=0.3,
        max_tokens=280,
    )

    answer = response.choices[0].message.content.strip()
    return clean_answer(answer)


def create_conversation_history():
    return [
        {
            "role": "system",
            "content": DEAKIN_SYSTEM_PROMPT,
        }
    ]


def add_user_message(history, text):
    history.append(
        {
            "role": "user",
            "content": text,
        }
    )


def add_assistant_message(history, text):
    history.append(
        {
            "role": "assistant",
            "content": text,
        }
    )


def trim_history(history, max_messages=10):
    """
    Keep system prompt + recent conversation.
    Prevents the conversation from getting too long.
    """
    if len(history) <= max_messages:
        return history

    system_prompt = history[0]
    recent_messages = history[-(max_messages - 1):]

    return [system_prompt] + recent_messages