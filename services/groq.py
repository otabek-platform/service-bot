from groq import AsyncGroq
from config import AI_SYSTEM_PROMPT

SYSTEM_MSG = {"role": "system", "content": AI_SYSTEM_PROMPT}
MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 4096


def get_client(api_key: str) -> AsyncGroq:
    return AsyncGroq(api_key=api_key)


async def chat_completion(api_key: str, messages: list[dict]) -> tuple[str, int]:
    client = get_client(api_key)
    full_messages = [SYSTEM_MSG] + messages

    response = await client.chat.completions.create(
        model=MODEL,
        messages=full_messages,
        max_tokens=MAX_TOKENS,
        temperature=0.7,
    )

    content = response.choices[0].message.content or ""
    tokens = response.usage.total_tokens if response.usage else 0
    return content, tokens
