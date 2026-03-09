from __future__ import annotations

from openai import OpenAI


class LMStudioClient:
    def __init__(self, base_url: str, model_name: str) -> None:
        self.client = OpenAI(base_url=base_url, api_key="lm-studio")
        self.model_name = model_name

    def close(self) -> None:
        self.client.close()

    def __del__(self) -> None:
        self.close()

    def complete(self, system_prompt: str, user_input: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""
