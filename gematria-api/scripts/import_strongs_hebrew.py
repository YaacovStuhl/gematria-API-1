from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Allow running this file directly (so `import app...` works on Windows).
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.gematria import compute_gematria, normalize_phrase


def _extract_json_from_js(js_text: str) -> str:
    """
    The file looks like:
      var strongsHebrewDictionary = {...};
    We strip the JS wrapper to get JSON.
    """
    # Find the first '{' and the last '}'.
    start = js_text.find("{")
    end = js_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Could not locate JSON object in JS file")
    return js_text[start : end + 1]


def _collapse_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _http_json(method: str, url: str, payload: dict | None = None, timeout: int = 60) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import Strong's Hebrew lemmas into Gematria API (phrase/value)."
    )
    parser.add_argument(
        "--dict-path",
        default=str(
            (Path(__file__).resolve().parents[2] / "external" / "strongs" / "hebrew" / "strongs-hebrew-dictionary.js")
        ),
        help="Path to strongs-hebrew-dictionary.js (from openscriptures/strongs)",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:5000", help="Gematria API base URL")
    parser.add_argument("--sleep", type=float, default=0.0, help="Sleep between API requests (seconds)")
    parser.add_argument("--max", type=int, default=0, help="If >0, stop after importing this many entries")
    parser.add_argument(
        "--progress-every",
        type=int,
        default=250,
        help="Print a progress line every N processed dictionary items (0 disables)",
    )
    args = parser.parse_args()

    dict_path = Path(args.dict_path)
    if not dict_path.exists():
        raise SystemExit(f"Dictionary file not found: {dict_path}")

    js_text = dict_path.read_text(encoding="utf-8", errors="strict")
    json_text = _extract_json_from_js(js_text)
    data = json.loads(json_text)

    base_url = args.base_url.rstrip("/")
    put_url = f"{base_url}/entries/by-phrase"

    upserted = 0
    failed = 0
    seen: set[str] = set()

    items = list(data.items())
    if args.max and args.max > 0:
        items = items[: args.max]

    for i, (strong_id, entry) in enumerate(items, start=1):
        lemma = str(entry.get("lemma") or "").strip()
        phrase = _collapse_spaces(normalize_phrase(lemma))
        if not phrase or phrase in seen:
            continue
        seen.add(phrase)

        value = compute_gematria(phrase)
        payload = {"phrase": phrase, "value": value, "source": f"strongs:{strong_id}"}

        try:
            _http_json("PUT", put_url, payload=payload)
            upserted += 1
        except urllib.error.HTTPError as e:
            failed += 1
            body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
            print(f"[{i}/{len(items)}] ERROR {e.code} for '{phrase}' ({strong_id}): {body}")
        except Exception as e:
            failed += 1
            print(f"[{i}/{len(items)}] ERROR for '{phrase}' ({strong_id}): {e}")

        if args.progress_every and args.progress_every > 0 and (i % args.progress_every == 0):
            print(
                f"[{i}/{len(items)}] progress: upserted={upserted}, failed={failed}, unique_phrases={len(seen)}",
                flush=True,
            )

        if args.sleep:
            time.sleep(args.sleep)

    print(f"Done. Upserted={upserted}, Failed={failed}, UniquePhrases={len(seen)}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())


