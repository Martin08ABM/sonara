"""Provider-independent bootstrap data contracts."""

from dataclasses import dataclass


def _nonempty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True)
class TextSegment:
    text: str
    start: int
    end: int

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text:
            raise ValueError("text must be a non-empty string")
        if (
            type(self.start) is not int
            or type(self.end) is not int
            or self.start < 0
            or self.end <= self.start
            or self.end - self.start != len(self.text)
        ):
            raise ValueError("invalid segment offsets")


@dataclass(frozen=True)
class Speaker:
    id: str
    name: str

    def __post_init__(self) -> None:
        _nonempty(self.id, "id")
        _nonempty(self.name, "name")


@dataclass(frozen=True)
class Emotion:
    label: str

    def __post_init__(self) -> None:
        _nonempty(self.label, "label")


@dataclass(frozen=True)
class VocalStyle:
    label: str

    def __post_init__(self) -> None:
        _nonempty(self.label, "label")


@dataclass(frozen=True)
class NarrationPlan:
    original_text: str
    segments: tuple[TextSegment, ...]

    def __post_init__(self) -> None:
        _nonempty(self.original_text, "original_text")
        if not isinstance(self.segments, tuple) or not self.segments:
            raise ValueError("segments must be a non-empty tuple")
        offset = 0
        for segment in self.segments:
            if not isinstance(segment, TextSegment):
                raise ValueError("segments must contain TextSegment instances")
            if (
                segment.start != offset
                or self.original_text[segment.start : segment.end] != segment.text
            ):
                raise ValueError("segments must cover the original text in order")
            offset = segment.end
        if offset != len(self.original_text):
            raise ValueError("segments must cover the original text in order")


@dataclass(frozen=True)
class ProviderCapabilities:
    name: str
    languages: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _nonempty(self.name, "name")
        if not isinstance(self.languages, tuple):
            raise ValueError("languages must be a tuple")
        for language in self.languages:
            _nonempty(language, "language")
