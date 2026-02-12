import argparse
import hashlib
from pathlib import Path
from typing import List, Dict
from utils.utils import *

import fasttext

# Text normalization
# ----------------------
def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = fix_mojibake(text)
    text = QUOTE_RE.sub('"', text) # replace rare quotes to --> ""
    text = text.replace("\u00a0", " ") # replace broken spaces
    text = WS_RE.sub(" ", text).strip() 
    text = HTML_TAG_RE.sub(" ", text)
    text = CIT_RE.sub(" ", text)
    text = PAREN_RE.sub(" ", text)
    return text

# Clean text. We already canonicalize it
def load_and_clean(
    raw_paths: List[Path],
    ft_model,
    min_chars: int,
    min_words: int,
) -> List[Dict]:
    seen_hashes = set()
    clean_docs = []
    for path in raw_paths:
        for row in read_jsonl(path):
            text = normalize_text(row.get("text", ""))
            if len(text) < min_chars or len(text.split()) < min_words:
                continue
            if not is_spanish(ft_model, text):
                continue
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if digest in seen_hashes:
                continue
            seen_hashes.add(digest)
            clean_docs.append(
                {
                    "source": row.get("source"),
                    "title": row.get("title", ""),
                    "text": text,
                }
            )
    return clean_docs
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wikipedia", type=str, default="data/raw/wikipedia_es/articles.jsonl")
    parser.add_argument("--scielo", type=str, default="data/raw/scielo/articles.jsonl")
    parser.add_argument("--clean-out", type=str, default="data/processed/clean.jsonl")
    parser.add_argument("--fasttext-path", type=str, default="models/fasttext/lid.176.bin")
    parser.add_argument("--min-chars", type=int, default=600)
    parser.add_argument("--min-words", type=int, default=120)

    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    raw_paths = [base_dir / args.wikipedia, base_dir / args.scielo]
    clean_out = base_dir / args.clean_out

    ft_model = fasttext.load_model(str(base_dir / args.fasttext_path))
    
    clean_docs = load_and_clean(raw_paths, ft_model, args.min_chars, args.min_words)
    write_jsonl(clean_out, clean_docs)


if __name__ == "__main__":
    main()