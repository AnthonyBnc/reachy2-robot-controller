from openai import OpenAI


# Paste your OpenRouter API key here.
# Example:
# OPENROUTER_API_KEY = "sk-or-v1-xxxxxxxxxxxxxxxx"
OPENROUTER_API_KEY = "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"


def main():
    if (
        not OPENROUTER_API_KEY
        or OPENROUTER_API_KEY == "PASTE_YOUR_OPENROUTER_API_KEY_HERE"
    ):
        print("❌ Please paste your OpenRouter API key into OPENROUTER_API_KEY.")
        return

    print("✅ API key found in file.")
    print("Testing OpenRouter API...")

    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": "http://localhost",
                "X-OpenRouter-Title": "Reachy Deakin Guide Test",
            },
        )

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": "What is Deakin University Openday?"
                }
            ],
            max_tokens=30,
        )

        print("✅ API request successful.")
        print("Model response:")
        print(response.choices[0].message.content)

    except Exception as e:
        print("❌ API request failed.")
        print("Error type:", type(e).__name__)
        print("Error message:", e)


if __name__ == "__main__":
    main()