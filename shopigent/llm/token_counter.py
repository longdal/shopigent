from dataclasses import dataclass

import litellm


@dataclass
class TokenCount:
    input_tokens: int
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


DEFAULT_MODEL = "gpt-3.5-turbo"


class TokenCounter:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def count_messages(self, messages: list[dict]) -> TokenCount:
        input_tokens = litellm.token_counter(model=self.model, messages=messages)
        return TokenCount(input_tokens=input_tokens)
