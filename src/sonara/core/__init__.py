"""Minimal text processing, without inference or audio generation."""

import logging

from sonara.models import NarrationPlan, TextSegment

logger = logging.getLogger(__name__)


class TextService:
    def process(self, text: str) -> NarrationPlan:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if not text.strip():
            raise ValueError("text must not be empty or whitespace only")
        segments = []
        offset = 0
        for line in text.splitlines(keepends=True):
            end = offset + len(line)
            segments.append(TextSegment(text=line, start=offset, end=end))
            offset = end
        logger.debug("Processed %d segments", len(segments))
        return NarrationPlan(original_text=text, segments=tuple(segments))
