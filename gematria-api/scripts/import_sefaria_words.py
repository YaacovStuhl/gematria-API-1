from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from pathlib import Path

# Allow running this file directly (so `import app...` works on Windows).
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.gematria import compute_gematria, normalize_phrase


HEBREW_WORD_RE = re.compile(r"[\u0590-\u05FF]+")


def _http_json(method: str, url: str, payload: dict | None = None, timeout: int = 30) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _flatten_sefaria_he(he_field) -> str:
    """
    Sefaria returns `he` as a string or nested lists (chapters/verses).
    Flatten to one big string for tokenization.
    """
    if he_field is None:
        return ""
    if isinstance(he_field, str):
        return he_field
    if isinstance(he_field, list):
        parts: list[str] = []
        for item in he_field:
            parts.append(_flatten_sefaria_he(item))
        return "\n".join(p for p in parts if p)
    return str(he_field)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Hebrew words from Sefaria into Gematria API.")
    parser.add_argument("--ref", required=True, help="Sefaria ref, e.g. 'Genesis.1' or 'Berakhot.2a'")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000", help="Gematria API base URL")
    parser.add_argument("--sleep", type=float, default=0.02, help="Sleep between API requests (seconds)")
    parser.add_argument("--max-words", type=int, default=0, help="If >0, stop after this many unique words")
    args = parser.parse_args()

    ref = args.ref
    base_url = args.base_url.rstrip("/")

    sefaria_url = f"https://www.sefaria.org/api/texts/{urllib.parse.quote(ref)}?lang=he&context=0"
    sefaria = _http_json("GET", sefaria_url)
    text = _flatten_sefaria_he(sefaria.get("he"))

    words = []
    seen: set[str] = set()
    for m in HEBREW_WORD_RE.finditer(text):
        raw = m.group(0)
        # Keep final-letter forms in the stored phrase; normalize only removes marks/punct.
        word = normalize_phrase(raw).strip()
        if not word:
            continue
        # normalize_phrase may return spaces if input had mixed chars; ensure single token
        if " " in word:
            word = word.replace(" ", "")
        if not word or word in seen:
            continue
        seen.add(word)
        words.append(word)
        if args.max_words and len(words) >= args.max_words:
            break

    print(f"Found {len(words)} unique Hebrew words in Sefaria ref '{ref}'.")

    put_url = f"{base_url}/entries/by-phrase"
    inserted = 0
    failed = 0

    for i, word in enumerate(words, start=1):
        value = compute_gematria(word)
        payload = {"phrase": word, "value": value, "source": f"sefaria:{ref}"}
        try:
            _http_json("PUT", put_url, payload=payload)
            inserted += 1
        except urllib.error.HTTPError as e:
            failed += 1
            body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
            print(f"[{i}/{len(words)}] ERROR {e.code} for '{word}': {body}")
        except Exception as e:
            failed += 1
            print(f"[{i}/{len(words)}] ERROR for '{word}': {e}")

        if args.sleep:
            time.sleep(args.sleep)

    print(f"Done. Upserted={inserted}, Failed={failed}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())


