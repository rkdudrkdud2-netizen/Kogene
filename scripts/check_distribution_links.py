"""분양처 URL의 HTTP 응답과 최종 이동 주소를 점검한다."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from distribution_sources import DISTRIBUTION_SOURCES  # noqa: E402


def check(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 qPCR-CrossCheck-LinkAudit/1.0"})
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read(250_000).decode("utf-8", errors="ignore")
            title_match = re.search(r"<title[^>]*>(.*?)</title>", body, flags=re.IGNORECASE | re.DOTALL)
            title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else ""
            return {
                "status": response.status,
                "final_url": response.url,
                "title": title[:160],
                "error": "",
            }
    except HTTPError as exc:
        return {"status": exc.code, "final_url": exc.url, "title": "", "error": str(exc)}
    except (URLError, TimeoutError, OSError) as exc:
        return {"status": 0, "final_url": url, "title": "", "error": str(exc)}


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    results = []
    for source in DISTRIBUTION_SOURCES:
        for field in ("url", "contact_url"):
            if not source.get(field):
                continue
            results.append({
                "acronym": source["acronym"],
                "field": field,
                "configured_url": source[field],
                **check(source[field]),
            })
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
