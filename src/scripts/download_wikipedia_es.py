from pathlib import Path
import json 
import argparse
from tqdm import tqdm 
from datasets import load_dataset


def create_wiki_json(limit:int, out_path: str, min_chars: int):
    # load the entire dataset of wikipedia (create the folder also)
    ds = load_dataset("wikimedia/wikipedia", "20231101.es", split="train")
    
    base_dir = Path(__file__).resolve().parent.parent  # /home/ronald/text-simplifier/src
    out_path = (base_dir / out_path).resolve()
    out_dir = out_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # open the json file in write mode, iterates over each document and save into the json 
    with open(out_path, "w", encoding="utf-8") as f:
        for i, row in enumerate(tqdm(ds)):
            if limit and i >= limit:
                break
            text = (row.get("text") or "").strip()
            title = (row.get("title") or "").strip()
            if len (text) < min_chars:
                continue
            json.dump(
                {"source":"wikipedia_es", "title":title, "text": text},
                f, ensure_ascii=False
            )
            f.write("\n")
            
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type = int, default=5000)
    parser.add_argument("--min-chars", type = int, default=500)
    parser.add_argument("--out", type=str, default="data/raw/wikipedia_es/articles.jsonl")
    args = parser.parse_args()
    create_wiki_json(args.limit, args.out, args.min_chars)

if __name__ == "__main__":
    main()
    