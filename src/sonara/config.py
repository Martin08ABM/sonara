"""Explicit, local configuration; importing this module has no side effects."""

import logging
import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        if self.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("Invalid log level")

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Settings":
        source = os.environ if environ is None else environ
        return cls(log_level=source.get("SONARA_LOG_LEVEL", "INFO").upper())

    def configure_logging(self) -> None:
        logging.basicConfig(level=getattr(logging, self.log_level))
