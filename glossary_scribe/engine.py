
from __future__ import annotations
import re
from typing import List, Dict, Any

def _extract_quotes(text: str) -> List[str]:
    # Extract text inside various quotes: “”, “” Chinese quotes; '' ""; also 〈〉 not included
    patterns = [
        r'“([^”]+)”', r'\"([^\"]+)\"', r'‘([^’]+)’', r'\'([^\']+)\'',
    ]
    found = []
    for pat in patterns:
        found += re.findall(pat, text)
    return list(dict.fromkeys([s.strip() for s in found if s.strip()]))  # dedupe preserve order

def _find_id(text: str) -> str | None:
    # Prefer explicit snake_case tokens preceding '中文名叫' or appearing as standalone like persona_state
    snake_candidates = re.findall(r'\b([a-z][a-z0-9_]+)\b', text)
    # Exclude common words
    blacklist = set(['ps','v2','v2_0'])
    snake_candidates = [c for c in snake_candidates if '_' in c and c not in blacklist]
    # Also avoid topics like ps.persona_state.v2.0
    topics = re.findall(r'\b([a-z]+\.[a-z0-9_]+\.[vV][0-9]+(?:\.[0-9]+)?)\b', text)
    topic_parts = set()
    for t in topics:
        parts = t.split('.')
        if len(parts) >= 2:
            topic_parts.add(parts[1])
    # choose first snake that matches topic second part or is near "中文名叫"
    # heuristic: if any snake equals a topic second part -> choose that
    for c in snake_candidates:
        if c in topic_parts:
            return c
    # fallback: first snake token
    if snake_candidates:
        return snake_candidates[0]
    return None

def _title_from_snake(snake: str) -> str:
    return ' '.join([w.capitalize() for w in snake.split('_')])

def _find_canonical_zh(text: str) -> str | None:
    m = re.search(r'中文名(?:叫|为|是)[“\"‘\']?([^”\"\']+)[”\"’\']?', text)
    if m:
        return m.group(1).strip()
    # fallback: pick first non-ascii quote content
    for q in _extract_quotes(text):
        if re.search(r'[\u4e00-\u9fff]', q):
            return q.strip()
    return None

def _find_canonical_en(text: str, id_guess: str | None) -> str | None:
    # Look for quoted ASCII phrases with spaces (e.g., Persona State)
    for q in _extract_quotes(text):
        if re.fullmatch(r'[A-Za-z][A-Za-z0-9 ]+[A-Za-z0-9]', q) and ' ' in q:
            return q.strip()
    # fallback from id
    if id_guess:
        return _title_from_snake(id_guess)
    return None

def _find_aliases(text: str, canonical_zh: str | None, canonical_en: str | None) -> List[str]:
    aliases = []
    # after cue words like 也叫/又称/别名/或
    cues = [r'(?:也叫|又称|别名|或|又名)']
    for cue in cues:
        for m in re.finditer(cue + r'([^。；；\n]+)', text):
            seg = m.group(1)
            # split by 顿号/逗号/“或”/和
            parts = re.split(r'[、,，/和或]|或', seg)
            for p in parts:
                cand = p.strip(' 。；;“”\'" ')
                if cand:
                    aliases.append(cand)
    # include quoted items
    for q in _extract_quotes(text):
        aliases.append(q.strip())
    # normalize: dedupe / remove canonicals / drop long phrases (>64) / keep ASCII words and CJK terms
    uniq = []
    seen = set()
    for a in aliases:
        if canonical_zh and a == canonical_zh: 
            continue
        if canonical_en and a == canonical_en:
            continue
        if len(a) > 64: 
            continue
        if a in seen: 
            continue
        seen.add(a)
        uniq.append(a)
    return uniq[:10]

def _find_topics(text: str) -> List[str]:
    topics = re.findall(r'\b([a-z]+\.[a-z0-9_]+\.[vV][0-9]+(?:\.[0-9]+)?)\b', text)
    return list(dict.fromkeys(topics))

def _derive_schemas_from_topics(topics: List[str]) -> List[str]:
    schemas = []
    for t in topics:
        parts = t.split('.')
        if len(parts) >= 3:
            ns, name = parts[0], parts[1]
            ver = '.'.join(parts[2:])  # keep full version like v2.0
            schemas.append(f"schemas/{ns}/events/{ns}.{name}.{ver}.schema.json")
    return schemas

def parse_text_to_terms(text: str) -> list[dict[str, Any]]:
    text = (text or "").strip()
    if not text:
        return []
    id_guess = _find_id(text) or "term"
    canonical_zh = _find_canonical_zh(text) or id_guess
    canonical_en = _find_canonical_en(text, id_guess) or id_guess.replace('_',' ').title()
    aliases = _find_aliases(text, canonical_zh, canonical_en)
    topics = _find_topics(text)
    if not topics:
        raise ValueError("No topics found in input text; cannot satisfy L0 topic requirement")
    schemas = _derive_schemas_from_topics(topics)
    rationale = None
    # Try to find rationale cues like 工程口径/理由/说明
    m = re.search(r'(?:工程口径|理由|说明)[:：]\s*([^。]+)', text)
    if m:
        rationale = m.group(1).strip()
    if not rationale:
        rationale = "Auto-extracted from free text; canonical names and bindings derived heuristically."
    item = {
        "id": id_guess,
        "canonical_zh": canonical_zh,
        "canonical_en": canonical_en,
        "aliases": aliases,
        "engineering_bindings": {
            "topics": topics,
            "schemas": schemas
        },
        "rationale": rationale
    }
    return [item]
