
from __future__ import annotations
from typing import Any, Dict, List
import json, os, re
from .engine import parse_text_to_terms

class NodeMolecule:
    """
    Minimal Node Molecule:
      - precheck(): L0 structural/bounds checks based on rules
      - invoke(text): run engine to produce terms list (list[dict])
      - postcheck(out): L2 properties (determinism, uniqueness, formats)
    """
    def __init__(self, spec_path: str):
        with open(spec_path, "r", encoding="utf-8") as f:
            self.spec = json.load(f)
        # repo root = package directory parent
        self.repo_root = os.path.dirname(os.path.dirname(__file__))

    def _load_l0_rules(self) -> Dict[str, Any]:
        path = self.spec["tck"]["l0"][0]
        if not os.path.isabs(path):
            path = os.path.join(self.repo_root, path)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def precheck(self) -> None:
        # ensure L0 rule file exists and has the keys we expect
        rules = self._load_l0_rules()
        for key in ["required_fields","id_pattern","topic_pattern","max_aliases","max_len"]:
            assert key in rules, f"L0 rule missing key: {key}"

    def invoke(self, text: str) -> List[Dict[str, Any]]:
        return parse_text_to_terms(text)

    def _iter_paths(self, data: Any, path_expr: str):
        """
        Extremely small JSONPath-like walker for patterns used in L2 rules:
        - "$[*].aliases[*]" etc.
        """
        if path_expr == "$":
            yield data
            return
        parts = [p for p in path_expr.split(".")]
        assert parts[0] == "$", f"only supports paths starting with $: {path_expr}"
        cur = [data]
        for p in parts[1:]:
            nxt = []
            if not cur:
                return
            if p.endswith("]"):
                # e.g., [*] or [0]
                name, idx = None, None
                if "[" in p:
                    name = p[:p.index("[")]
                    sel = p[p.index("[")+1:-1]
                else:
                    name, sel = p, None
                for obj in cur:
                    if name:
                        if isinstance(obj, dict) and name in obj:
                            obj = obj[name]
                        else:
                            continue
                    if sel == "*":
                        if isinstance(obj, list):
                            for it in obj:
                                nxt.append(it)
                        else:
                            continue
                    elif sel is None:
                        nxt.append(obj)
                    else:
                        try:
                            i = int(sel)
                            if isinstance(obj, list) and 0 <= i < len(obj):
                                nxt.append(obj[i])
                        except:
                            pass
            else:
                for obj in cur:
                    if isinstance(obj, dict) and p in obj:
                        nxt.append(obj[p])
            cur = nxt
        for obj in cur:
            yield obj

    def _regex_all(self, items, pattern: str) -> bool:
        rx = re.compile(pattern)
        for it in items:
            if not isinstance(it, str) or rx.fullmatch(it) is None:
                return False
        return True

    def _l0_check_output(self, out: List[Dict[str, Any]], rules: Dict[str, Any]) -> None:
        assert isinstance(out, list) and len(out) >= 1, "output must be a non-empty list"
        for item in out:
            # required fields
            for k in rules["required_fields"]:
                assert k in item, f"missing field: {k}"
            assert re.fullmatch(rules["id_pattern"], item["id"]), f"id not snake_case: {item['id']}"
            assert len(item["id"]) <= rules["max_len"]["id"]
            assert len(item["canonical_zh"]) <= rules["max_len"]["canonical_zh"]
            assert len(item["canonical_en"]) <= rules["max_len"]["canonical_en"]
            topics = item.get("engineering_bindings",{}).get("topics",[])
            assert topics, "topics required"
            for t in topics:
                assert re.fullmatch(rules["topic_pattern"], t), f"topic format invalid: {t}"
            aliases = item.get("aliases",[])
            assert len(aliases) <= rules["max_aliases"], "too many aliases"
            if rules.get("forbid_alias_equals_canonical", False):
                assert item["canonical_zh"] not in aliases, "alias equals canonical_zh"
                assert item["canonical_en"] not in aliases, "alias equals canonical_en"

    def _l2_properties(self, out: List[Dict[str, Any]], props: Dict[str, Any]) -> None:
        # deterministic: run N-1 more times with same input hashed from first item rationale to reconstruct input? 
        # In our tck runner we'll handle determinism by re-running invoke on the given text.
        # Here only structural checks:
        # aliases unique:
        for item in out:
            aliases = item.get("aliases", [])
            assert len(set(aliases)) == len(aliases), "aliases must be unique"
        # Additional checks are executed in tck_runner where we know the input text.

    def postcheck(self, out: List[Dict[str, Any]]) -> None:
        rules = self._load_l0_rules()
        self._l0_check_output(out, rules)
        # L2 additional checks reside in tck_runner for convenience

def load_spec() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "specs", "node-molecule.spec.json")
