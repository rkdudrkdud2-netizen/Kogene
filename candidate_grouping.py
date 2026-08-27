"""웹 후보 목록을 대표 병원체 단위로 안전하게 요약한다."""

from __future__ import annotations

from collections import OrderedDict
import re


PRIORITY_ORDER = {"필수": 0, "권장": 1, "참고": 2}
_QUALIFIER = re.compile(
    r"\s+(?:subsp\.?|subspecies|ssp\.?|strain|str\.?|serotype|serovar|biovar|"
    r"genotype|isolate|variant|type)\b.*$",
    re.IGNORECASE,
)
_TYPED_VIRUS = re.compile(
    r"^(.*(?:virus|rotavirus|norovirus|adenovirus|astrovirus|sapovirus))\s+"
    r"(?:[A-Z]\d*|G\d+|GI{1,3}|F?\d+(?:/\d+)?)$",
    re.IGNORECASE,
)
_BINOMIAL = re.compile(r"^([A-Z][A-Za-z-]+\s+[a-z][A-Za-z-]+)(?:\s+.+)$")


def representative_organism_name(name: str) -> str:
    """strain·아종·혈청형·유전형 표기를 제거한 표시용 대표 병원체명을 반환한다."""
    cleaned = " ".join(str(name or "").split()).strip(" ;,")
    if not cleaned:
        return "—"
    without_qualifier = _QUALIFIER.sub("", cleaned).strip(" ;,")
    if without_qualifier != cleaned:
        return without_qualifier
    typed_virus = _TYPED_VIRUS.match(cleaned)
    if typed_virus:
        return typed_virus.group(1).strip()
    binomial = _BINOMIAL.match(cleaned)
    if binomial:
        return binomial.group(1)
    return cleaned


def _split_values(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (tuple, list, set)):
        values = value
    else:
        values = re.split(r"\s*[,;]\s*", str(value))
    return [str(item).strip() for item in values if str(item).strip() not in {"", "—"}]


def group_candidate_rows(rows: list[dict]) -> list[dict]:
    """후보 세부 행을 대표 병원체별 요약 행으로 집계한다."""
    grouped: OrderedDict[str, list[dict]] = OrderedDict()
    for row in rows:
        representative = representative_organism_name(row.get("organism", ""))
        grouped.setdefault(representative, []).append(row)

    output = []
    for representative, members in grouped.items():
        priorities = [item.get("우선순위", "참고") for item in members]
        management_ids = list(dict.fromkeys(
            value for item in members for value in _split_values(item.get("관리번호"))
        ))
        related_targets = list(dict.fromkeys(
            value for item in members for value in _split_values(item.get("input_targets"))
        ))
        relations = list(dict.fromkeys(
            str(item.get("relation", "")).strip() for item in members if str(item.get("relation", "")).strip()
        ))
        detail_names = list(dict.fromkeys(str(item.get("organism", "")).strip() for item in members))
        output.append({
            "우선순위": min(priorities, key=lambda value: PRIORITY_ORDER.get(value, 99)),
            "대표 병원체": representative,
            "세부 후보 수": len(members),
            "포함 세부 후보": "; ".join(detail_names),
            "관련 입력 표적": " + ".join(related_targets) or "—",
            "분류": ", ".join(relations) or "—",
            "보유 여부": "보유" if any(item.get("보유 여부") == "보유" for item in members) else "미보유",
            "보유 자원 수": len(management_ids) if management_ids else sum(
                int(item.get("보유 자원 수", 0) or 0) for item in members
            ),
            "관리번호": ", ".join(management_ids) or "—",
        })
    return output
