import json
import logging

from omni.llm.client import call_llm

logger = logging.getLogger(__name__)


def safe_call_llm_json(prompt: str) -> dict:
    for _ in range(5):
        raw_answer = call_llm(prompt)
        try:
            answer = json.loads(raw_answer)
            return answer
        except Exception as e:
            logger.exception("Failed to parse LLM JSON response")
            logger.info("Trying again...")

    logger.error("Tried to call LLM JSON 5 times but failed")
    raise ValueError("Tried to call LLM JSON 5 times but failed")
