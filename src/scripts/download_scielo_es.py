from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import json
import argparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import trafilatura

SEARCH_URL = "https://search.scielo.org/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://search.scielo.org/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

def main(query: str, limit:int, out_path: str, min_chars:int):
    
    base_dir = Path(__file__).resolve().parent.parent  # /home/ronald/text-simplifier/src
    out_path = (base_dir / out_path).resolve()
    out_dir = out_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    urls = find_article_links(query,limit)
    with open (out_path, "w", encoding="utf-8") as f:
        for url in tqdm(urls):
            text,title = fetch_article_info(url)
        
            if not text or len(text) < min_chars:
                continue
            json.dump(
                {"source": "scielo", "url": url, "title": title, "text": text},
                f, ensure_ascii=False
            )
            f.write("\n")

def find_article_links (query: str, limit:int):
    links, step, start = set(), 50, 0
    while len(links) < limit: 
        params = {"q": query, "lang": "es", "count": step, "from": start, "output":"site", "format":"summary","filter[la][]": "es"}
        r = requests.get(SEARCH_URL, params=params, headers=HEADERS,timeout=30)

        soup = BeautifulSoup(r.text, "html.parser")
        
        for a in soup.find_all("a", href=True):
            href = canonicalize_url(a.get("href"))
            if href:
                links.add(href)
                if len(links) >= limit:
                    break
        if step + start >= 2000 or not soup.find_all("a", href=True):
            break
        start += step
    return list(links)

def canonicalize_url(href: str) -> str:
    """Extract unique pid of article."""
    if not href:
        return ""
    u = urlparse(href)
    if "scielo.php" in u.path:
        qs = parse_qs(u.query)
        pid = qs.get("pid", [None])[0]
        script = qs.get("script", [None])[0]
        if pid and script == "sci_arttext":
            return urlunparse((u.scheme, u.netloc, u.path, "", 
                             urlencode({"script": "sci_arttext", "pid": pid}), ""))
    if "/article/" in href:
        return href.rstrip("/")
    return ""

def fetch_article_info(url:str):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text,"html.parser")
        title_el = soup.select_one('p.title')
        title = title_el.get_text(separator=" ", strip=True) if title_el else ""
        
        text = trafilatura.extract(r.text, include_comments=False,include_tables=False)
        return (text,title)
    except Exception:
        return None,None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default="*")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--min-chars", type=int, default=800)
    parser.add_argument("--out", type=str, default="data/raw/scielo/articles.jsonl")
    args = parser.parse_args()
    main(args.query, args.limit, args.out, args.min_chars)
        
    
            