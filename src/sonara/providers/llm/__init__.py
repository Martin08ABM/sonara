"""Interface for a future language model provider."""

from typing import Protocol

from sonara.models import ProviderCapabilities


class LLMProvider(Protocol):
    def capabilities(self) -> ProviderCapabilities: ...

    def complete(self, prompt: str) -> str: ...
