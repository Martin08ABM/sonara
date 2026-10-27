"""Interface for a future speech synthesis provider."""

from typing import Protocol

from sonara.models import ProviderCapabilities, TextSegment


class TTSProvider(Protocol):
    def capabilities(self) -> ProviderCapabilities: ...

    def synthesize(self, segment: TextSegment) -> bytes: ...
