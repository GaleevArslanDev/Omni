import ollama

def call_llm(prompt: str) -> str:
    response = ollama.chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты управляешь Minecraft-агентом. "
                    "Верни только один JSON-объект. "
                    "Без markdown. Без объяснений."
                )
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        options={
            "temperature": 0,
            "num_predict": 1000,
        },
        think=False,
    )

    return response["message"]["content"] or ""