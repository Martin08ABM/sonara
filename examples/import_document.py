"""Import a local document without models: python examples/import_document.py FILE [JSON]."""

import argparse
from pathlib import Path

from sonara.content import ContentError, ContentService

parser = argparse.ArgumentParser(description="Inspect a local Sonara document")
parser.add_argument("file", type=Path)
parser.add_argument("json_output", type=Path, nargs="?")
args = parser.parse_args()
try:
    document = ContentService().import_file(args.file)
except ContentError as error:
    parser.exit(1, f"{error.code}: {error.message}\n")
print(f"Format: {document.format}")
print(f"Title: {document.title or '(not available)'}")
print(f"Sections: {len(document.sections)}")
print(f"Fragments: {len(document.fragments)}")
print(f"First fragment: {document.fragments[0].text!r}")
if args.json_output:
    args.json_output.write_text(document.to_json(), encoding="utf-8")
    print(f"JSON: {args.json_output}")
