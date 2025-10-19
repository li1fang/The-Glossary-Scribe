
from __future__ import annotations
import sys
from .engine import parse_text_to_terms
from .yaml_utils import to_yaml

def main():
    text = sys.stdin.read()
    try:
        items = parse_text_to_terms(text)
    except ValueError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        sys.exit(1)
    yaml_str = to_yaml(items)
    sys.stdout.write(yaml_str)

if __name__ == "__main__":
    main()
