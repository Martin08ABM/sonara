from typing import cast

import pytest

from sonara import Settings, TextService
from sonara.classifiers import ExpressiveClassifier
from sonara.models import (
    Emotion,
    NarrationPlan,
    ProviderCapabilities,
    Speaker,
    TextSegment,
    VocalStyle,
)
from sonara.providers.llm import LLMProvider
from sonara.providers.tts import TTSProvider


class FakeLLM:
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities("fake-llm", ("en",))

    def complete(self, prompt: str) -> str:
        return f"fake: {prompt}"


class FakeTTS:
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities("fake-tts")

    def synthesize(self, segment: TextSegment) -> bytes:
        return segment.text.encode()


class FakeClassifier:
    def classify(self, segment: TextSegment) -> tuple[Emotion, VocalStyle]:
        return Emotion("neutral"), VocalStyle("normal")


@pytest.mark.parametrize("text", ["Hello", "a\r\n\r\nb\n", " á\u2028你好\n", "\ntext\n"])
def test_text_is_preserved(text: str) -> None:
    plan = TextService().process(text)
    assert plan.original_text == text
    assert "".join(s.text for s in plan.segments) == text
    assert all(text[s.start : s.end] == s.text for s in plan.segments)


@pytest.mark.parametrize("text", ["", " \n\t"])
def test_blank_text_rejected(text: str) -> None:
    with pytest.raises(ValueError):
        TextService().process(text)


def test_non_string_rejected() -> None:
    with pytest.raises(TypeError):
        TextService().process(cast(str, None))


def test_contract_validation() -> None:
    with pytest.raises(ValueError):
        TextSegment("ab", 0, 1)
    with pytest.raises(ValueError):
        NarrationPlan("ab", (TextSegment("b", 1, 2),))
    with pytest.raises(ValueError):
        NarrationPlan("ab", (TextSegment("a", 0, 1),))
    with pytest.raises(ValueError):
        Speaker("", "name")
    with pytest.raises(ValueError):
        Emotion(" ")
    with pytest.raises(ValueError):
        VocalStyle("")
    with pytest.raises(ValueError):
        ProviderCapabilities("fake", ("",))
    assert Speaker("1", "Ana").name == "Ana"


def test_fake_providers_satisfy_interfaces() -> None:
    llm: LLMProvider = FakeLLM()
    tts: TTSProvider = FakeTTS()
    classifier: ExpressiveClassifier = FakeClassifier()
    segment = TextSegment("hello", 0, 5)
    assert llm.capabilities().languages == ("en",)
    assert llm.complete(segment.text) == "fake: hello"
    assert tts.capabilities().name == "fake-tts"
    assert tts.synthesize(segment) == b"hello"
    assert classifier.classify(segment) == (Emotion("neutral"), VocalStyle("normal"))


def test_configuration() -> None:
    assert Settings.from_env({}).log_level == "INFO"
    assert Settings.from_env({"SONARA_LOG_LEVEL": "debug"}).log_level == "DEBUG"
    with pytest.raises(ValueError):
        Settings.from_env({"SONARA_LOG_LEVEL": "not-a-level"})
