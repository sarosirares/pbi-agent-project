import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


class VLLMClient:

    def __init__(self) -> None:
        # Load vLLM connection settings from the local .env file.
        load_dotenv()

        self.base_url = os.getenv("VLLM_BASE_URL")
        self.api_key = os.getenv("VLLM_API_KEY")
        self.model_name = os.getenv("VLLM_MODEL")

        # Stop early if the application is missing required configuration.
        if not all((self.base_url, self.api_key, self.model_name)):
            raise RuntimeError(
                "Required VLLM configuration is missing from the .env file."
            )

        # vLLM exposes an OpenAI-compatible API, so we can use
        # the OpenAI Python client with our own base URL.
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=60.0,
        )

    def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.0,
        enable_thinking: bool = False,
        timeout_seconds: float | None = None,
    ) -> Any:

        if max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero.")

        client = self.client

        if timeout_seconds is not None:
            if timeout_seconds <= 0:
                raise ValueError(
                    "timeout_seconds must be "
                    "greater than zero."
                )

            client = self.client.with_options(
                timeout=timeout_seconds,
                max_retries=0,
            )

        return client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,

            # Forward the Qwen thinking-mode setting through vLLM.
            extra_body={
                "chat_template_kwargs": {
                    "enable_thinking": enable_thinking,
                }
            },
        )