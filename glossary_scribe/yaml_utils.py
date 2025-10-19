
from __future__ import annotations
from typing import Any, Dict, List

def _yaml_escape(s: str) -> str:
    # naive escape for quotes and backslashes
    return s.replace("\\", "\\\\").replace("\"", "\\\"")

def _emit_value(v: Any, indent: int) -> str:
    sp = " " * indent
    if isinstance(v, dict):
        lines = []
        for i, (k, val) in enumerate(v.items()):
            if isinstance(val, (dict, list)):
                lines.append(f"{sp}{k}:")
                lines.append(_emit_value(val, indent + 2))
            else:
                if isinstance(val, str):
                    lines.append(f'{sp}{k}: "{_yaml_escape(val)}"')
                elif isinstance(val, bool):
                    lines.append(f"{sp}{k}: " + ("true" if val else "false"))
                else:
                    lines.append(f"{sp}{k}: {val}")
        return "\n".join(lines)
    elif isinstance(v, list):
        lines = []
        for item in v:
            if isinstance(item, (dict, list)):
                lines.append(" " * indent + "-")
                lines.append(_emit_value(item, indent + 2))
            else:
                if isinstance(item, str):
                    lines.append(" " * indent + f'- "{_yaml_escape(item)}"')
                elif isinstance(item, bool):
                    lines.append(" " * indent + f"- " + ("true" if item else "false"))
                else:
                    lines.append(" " * indent + f"- {item}")
        return "\n".join(lines)
    else:
        if isinstance(v, str):
            return sp + f"\"{_yaml_escape(v)}\""
        elif isinstance(v, bool):
            return sp + ("true" if v else "false")
        else:
            return sp + str(v)

def to_yaml(obj: Any) -> str:
    # Expect obj to be list[dict] (terms list); keep stable field order
    return _emit_value(obj, 0) + "\n"
