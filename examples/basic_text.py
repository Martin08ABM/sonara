"""Process text without loading a model or connecting to a provider."""

from sonara import Settings, TextService

Settings.from_env().configure_logging()
plan = TextService().process("Hello.\nWelcome to Sonara.")
for segment in plan.segments:
    print(f"{segment.start}:{segment.end}: {segment.text!r}")
