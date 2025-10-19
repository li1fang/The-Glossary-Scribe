
import os
from glossary_scribe.tck_runner import run_all
from glossary_scribe.engine import parse_text_to_terms

if __name__ == "__main__":
    run_all()
    base = os.path.join(os.path.dirname(__file__), "tck", "l1", "missing_topics_input.txt")
    with open(base, "r", encoding="utf-8") as f:
        missing_topics_text = f.read()
    try:
        parse_text_to_terms(missing_topics_text)
    except ValueError:
        print("OK: L0/L1/L2 all green and missing-topic case rejected.")
    else:
        raise AssertionError("missing_topics_input should raise ValueError but did not")
