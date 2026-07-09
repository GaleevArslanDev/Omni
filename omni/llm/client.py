import ollama

from omni.config import LLM_MODEL, LLM_NUM_PREDICT, LLM_TEMPERATURE


def call_llm(prompt: str) -> str:
    response = ollama.chat(
        model=LLM_MODEL,
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
            "temperature": LLM_TEMPERATURE,
            "num_predict": LLM_NUM_PREDICT,
        },
        think=False,
    )

    return response["message"]["content"] or ""
