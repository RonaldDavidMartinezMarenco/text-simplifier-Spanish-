import json
import re
import unicodedata
from pathlib import Path
from typing import Iterable, List, Dict, Tuple, Optional

# NORMALIZATION PATTERNS
MOJIBAKE_RE = re.compile(r"[ÂÃÄÅæøßþð]")
HTML_TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+") # whitespaces
CIT_RE = re.compile(r"\[[0-9,\s]+\]") # quotes
PAREN_RE = re.compile(r"\([^)]{10,}\)") # parentheses at least with 10 characters
QUOTE_RE = re.compile(r"“|”|«|»") 

# ----------------------
# IO utils
# ----------------------
def read_jsonl(path: Path) -> Iterable[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line) # we use it to not overload the memory

def write_jsonl(path: Path, rows: Iterable[Dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            json.dump(r, f, ensure_ascii=False)
            f.write("\n")
            
# ----------------------
# Language filter (fastText)
# ----------------------
def is_spanish(ft_model, text: str, threshold: float = 0.7) -> bool:
    if not text:
        return False
    labels, probs = ft_model.predict(text.replace("\n", " ")[:2000])
    if not labels:
        return False
    return labels[0] == "__label__es" and probs[0] >= threshold

# ----------------------
# Clean rare characters
# ----------------------
def fix_mojibake(text: str) -> str:
    if not text or not MOJIBAKE_RE.search(text):
        return text
    return text.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
