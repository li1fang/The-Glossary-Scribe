
from __future__ import annotations
import os, json, glob, hashlib, re
from typing import List, Dict, Any
from .node_molecule import NodeMolecule, load_spec
from .engine import parse_text_to_terms

def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _json(path: str) -> Any:
    return json.loads(_read(path))

def run_l0(node: NodeMolecule) -> None:
    node.precheck()

def run_l1(node: NodeMolecule) -> None:
    # find *_input.txt and corresponding *_expected.json
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tck", "l1")
    inputs = glob.glob(os.path.join(base, "*_input.txt"))
    assert inputs, "no L1 inputs found"
    for ipath in inputs:
        name = os.path.basename(ipath).replace("_input.txt", "")
        epath = os.path.join(base, f"{name}_expected.json")
        assert os.path.exists(epath), f"expected not found for {name}"
        text = _read(ipath)
        expected = _json(epath)
        if isinstance(expected, dict) and "expect_error" in expected:
            try:
                node.invoke(text)
            except Exception as exc:
                assert exc.__class__.__name__ == expected["expect_error"], (
                    f"{name} expected {expected['expect_error']} but got {exc.__class__.__name__}"
                )
                message_contains = expected.get("message_contains")
                if message_contains is not None:
                    assert message_contains in str(exc), (
                        f"{name} expected error message containing '{message_contains}'"
                    )
            else:
                raise AssertionError(f"{name} expected to raise {expected['expect_error']}")
            continue
        out = node.invoke(text)
        # Compare with normalization
        assert isinstance(out, list) and isinstance(expected, list), "both outputs must be lists"
        assert len(out) == len(expected), f"length mismatch for {name}"
        for i, (a, b) in enumerate(zip(out, expected)):
            # canonical compare ignoring order in aliases/topics/schemas
            def norm(d):
                d2 = dict(d)
                eb = d2.get("engineering_bindings", {})
                if "aliases" in d2 and isinstance(d2["aliases"], list):
                    d2["aliases"] = sorted(d2["aliases"])
                if "engineering_bindings" in d2:
                    if "topics" in eb and isinstance(eb["topics"], list):
                        eb["topics"] = sorted(eb["topics"])
                    if "schemas" in eb and isinstance(eb.get("schemas"), list):
                        eb["schemas"] = sorted(eb["schemas"])
                    d2["engineering_bindings"] = eb
                return d2
            assert norm(a) == norm(b), f"L1 mismatch for {name}: {norm(a)} != {norm(b)}"

def run_l2(node: NodeMolecule) -> None:
    # deterministic and property checks
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tck")
    props = _json(os.path.join(base, "l2", "properties.json"))
    # Use first L1 input as the deterministic anchor
    ipath = glob.glob(os.path.join(base, "l1", "*_input.txt"))[0]
    text = _read(ipath)
    runs = []
    for _ in range(props.get("deterministic_runs", 3)):
        runs.append(node.invoke(text))
    # determinism: all runs equal
    first = json.dumps(runs[0], ensure_ascii=False, sort_keys=True)
    for i, r in enumerate(runs[1:], start=2):
        assert json.dumps(r, ensure_ascii=False, sort_keys=True) == first, f"non-deterministic output at run {i}"
    # structural property checks
    out = runs[0]
    # uniqueness of aliases
    for item in out:
        aliases = item.get("aliases", [])
        assert len(set(aliases)) == len(aliases), "aliases must be unique"
        # alias must not equal canonical names
        assert item.get("canonical_zh") not in aliases, "alias duplicates canonical_zh"
        assert item.get("canonical_en") not in aliases, "alias duplicates canonical_en"
        # id snake_case
        assert re.fullmatch(r"^[a-z][a-z0-9_]*$", item.get("id","")), "id must be snake_case"
        # topics format
        for t in item.get("engineering_bindings",{}).get("topics",[]):
            assert re.fullmatch(r"^[a-z]+\.[a-z0-9_]+\.[vV][0-9]+(\.[0-9]+)?$", t), f"bad topic {t}"

def run_all() -> None:
    node = NodeMolecule(load_spec())
    run_l0(node)
    run_l1(node)
    run_l2(node)

if __name__ == "__main__":
    run_all()
    print("TCK L0/L1/L2: ALL GREEN")
