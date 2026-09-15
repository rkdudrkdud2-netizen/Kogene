"""보수적인 PubMed 근거 검색 보조 기능.

검색 결과가 여러 독립 문헌에서 한 병원체군으로 명확히 모일 때만 자동
분류 후보를 반환한다. 결과가 부족하거나 경합하면 사용자가 확인하도록
남기며, 유전자명만으로 추측하지 않는다.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


PUBMED_SEARCH = "https://pubmed.ncbi.nlm.nih.gov/?term={}"
ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# 자동 분류 범위는 현재 앱이 검증 패널을 보유한 병원체군으로 제한한다.
REFERENCE_ORGANISMS = {
    "STEC/EHEC": ("shiga toxin-producing escherichia coli", "stec", "ehec"),
    "Shigella/EIEC": ("shigella", "enteroinvasive escherichia coli", "eiec"),
    "Salmonella": ("salmonella",),
    "Campylobacter": ("campylobacter",),
    "Clostridioides difficile": ("clostridioides difficile", "clostridium difficile"),
    "Listeria": ("listeria",),
    "Norovirus": ("norovirus",),
    "Rotavirus": ("rotavirus",),
    "SARS-CoV-2": ("sars-cov-2", "2019-ncov", "covid-19"),
    "Influenza": ("influenza",),
    "RSV": ("respiratory syncytial virus",),
    "Bordetella pertussis": ("bordetella pertussis",),
    "Mycoplasma pneumoniae": ("mycoplasma pneumoniae",),
    "Plasmodium": ("plasmodium", "malaria"),
    "Babesia": ("babesia",),
}


def _read_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "qPCR-CrossCheck/1.0 (literature lookup)"})
    with urlopen(request, timeout=12) as response:
        return json.loads(response.read().decode("utf-8"))


def _article_score(title: str) -> set[str]:
    text = re.sub(r"\s+", " ", title.casefold())
    return {
        organism for organism, aliases in REFERENCE_ORGANISMS.items()
        if any(re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", text) for alias in aliases)
    }


def resolve_from_articles(query: str, articles: list[dict]) -> dict:
    """문헌 제목별 병원체 언급을 집계해 보수적으로 한 후보만 채택한다."""
    counts: Counter[str] = Counter()
    for article in articles:
        for organism in _article_score(article.get("title", "")):
            counts[organism] += 1
    ranked = counts.most_common()
    search_url = PUBMED_SEARCH.format(quote(query))
    if not ranked or ranked[0][1] < 2:
        return {"status": "insufficient", "query": query, "articles": articles,
                "search_url": search_url, "counts": dict(counts)}
    leader, leader_count = ranked[0]
    runner_up = ranked[1][1] if len(ranked) > 1 else 0
    if runner_up and leader_count < runner_up * 2:
        return {"status": "ambiguous", "query": query, "articles": articles,
                "search_url": search_url, "counts": dict(counts)}
    return {"status": "resolved", "query": query, "organism": leader,
            "support_count": leader_count, "articles": articles,
            "search_url": search_url, "counts": dict(counts)}


def search_pubmed_target(query: str, max_results: int = 10) -> dict:
    """PubMed 최신 검색을 수행하고 충분한 문헌 일치가 있을 때만 분류한다."""
    cleaned = (query or "").strip()
    search_term = f'("{cleaned}"[Title/Abstract]) AND (PCR[Title/Abstract] OR qPCR[Title/Abstract] OR diagnostic*[Title/Abstract])'
    try:
        params = urlencode({"db": "pubmed", "retmode": "json", "retmax": max_results,
                            "sort": "relevance", "term": search_term})
        ids = _read_json(f"{ESEARCH}?{params}").get("esearchresult", {}).get("idlist", [])
        if not ids:
            return resolve_from_articles(cleaned, [])
        summary_params = urlencode({"db": "pubmed", "retmode": "json", "id": ",".join(ids)})
        payload = _read_json(f"{ESUMMARY}?{summary_params}").get("result", {})
        articles = [
            {"pmid": pmid, "title": payload.get(pmid, {}).get("title", ""),
             "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"}
            for pmid in ids if payload.get(pmid)
        ]
        return resolve_from_articles(cleaned, articles)
    except Exception as exc:  # 네트워크 장애가 전체 앱 실행을 막지 않게 한다.
        return {"status": "error", "query": cleaned, "error": str(exc),
                "articles": [], "search_url": PUBMED_SEARCH.format(quote(cleaned))}
