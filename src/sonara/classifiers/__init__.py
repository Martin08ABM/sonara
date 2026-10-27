"""Interface isolating future expressive classification, initially using Laya."""

from typing import Protocol

from sonara.models import Emotion, TextSegment, VocalStyle


class ExpressiveClassifier(Protocol):
    def classify(self, segment: TextSegment) -> tuple[Emotion, VocalStyle]: ...
