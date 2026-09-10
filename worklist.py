"""Single·Multiplex qPCR 공통 시험 작업 목록 생성."""

from __future__ import annotations

import math
import re


WORKLIST_COLUMNS = (
    "입력 표적", "질환군", "병원체 유형", "검증 구분", "우선순위", "추천 미생물",
    "보유 여부", "관리번호", "사내 자원명", "Cat no.", "구매일",
    "최초 원액 용량 (µL)", "원액 누적 사용량 (µL)", "원액 잔량 (µL)",
    "희석액(1/100) 튜브 수 (n)", "준비 상태", "재고 점검", "비고", "매칭 점수",
)


def parse_quantity(value) -> float | None:
    """µL 또는 튜브 수 값을 숫자로 정규화하며 '소진'은 0으로 처리한다."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.casefold() in {"nan", "none", "-", "—"}:
        return None
    if "소진" in text:
        return 0.0
    match = re.search(r"-?\d[\d,]*(?:\.\d+)?", text)
    return float(match.group(0).replace(",", "")) if match else None


def _display_number(value: float | None):
    if value is None:
        return None
    return int(value) if float(value).is_integer() else round(value, 3)


def _display_provided_number(value):
    """원본에 실제 숫자가 적힌 경우에만 보고서용 수치로 반환한다.

    ``소진``은 준비 상태를 판단할 때는 0으로 해석할 수 있지만, 사용자가
    제공한 수치 0은 아니다. 따라서 수치 열에는 빈칸으로 남겨 프로그램이
    임의로 재고량을 만들어 낸 것처럼 보이지 않게 한다.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.casefold() in {"nan", "none", "<na>", "nat", "-", "—"}:
        return None
    if not re.search(r"-?\d[\d,]*(?:\.\d+)?", text):
        return None
    return _display_number(parse_quantity(text))


def _match_value(match, field: str, default=""):
    """서버 재시작 전 생성된 구형 MatchResult도 안전하게 읽는다."""
    if isinstance(match, dict):
        value = match.get(field, default)
    else:
        value = getattr(match, field, default)
    return default if value is None else value


def resource_readiness(match) -> tuple[str, str]:
    """자원의 시험 준비 상태와 재고 수치 점검 결과를 반환한다."""
    initial_volume = _match_value(match, "initial_volume_ul")
    cumulative_use = _match_value(match, "cumulative_use_ul")
    remaining_volume = _match_value(match, "remaining_volume_ul")
    dilution_tubes = _match_value(match, "dilution_tubes")
    initial = parse_quantity(initial_volume)
    used = parse_quantity(cumulative_use)
    remaining = parse_quantity(remaining_volume)
    tubes = parse_quantity(dilution_tubes)

    if tubes is not None and tubes > 0:
        readiness = "즉시 사용 가능"
    elif remaining is not None and remaining > 0:
        readiness = "희석 필요" if str(dilution_tubes).strip() else "원액 사용 가능"
    elif remaining == 0 and (tubes is None or tubes == 0):
        readiness = "소진"
    else:
        readiness = "정보 확인 필요"

    check = "정상"
    if all(value is not None for value in (initial, used, remaining)):
        expected = max(0.0, initial - used)
        if not math.isclose(expected, remaining, abs_tol=0.1):
            check = f"수치 불일치 (계산 잔량 {expected:g} µL)"
    notes = str(_match_value(match, "notes")).casefold()
    if check == "정상" and any(term in notes for term in ("확인", "맞지 않", "불일치")):
        check = "비고 확인 필요"
    return readiness, check


def build_worklist_rows(results, assay_type: str, target: str) -> list[dict]:
    """추천 미생물별 모든 매칭 자원을 한 행씩 펼친 작업 목록으로 만든다."""
    rows = []
    for item in results:
        related_targets = item.get("input_targets") or (target,)
        target_label = " + ".join(str(value) for value in related_targets if str(value).strip()) or target or "—"
        matches = item.get("자원 상세", [])
        if not matches:
            rows.append({
                "입력 표적": target_label,
                "질환군": item.get("system", "기타"),
                "병원체 유형": item.get("kind", "미분류"),
                "검증 구분": item.get("검증 구분", "특이도"),
                "우선순위": item.get("우선순위", "참고"),
                "추천 미생물": item["organism"],
                "보유 여부": "미보유",
                "관리번호": "—",
                "사내 자원명": "—",
                "Cat no.": "—",
                "구매일": "—",
                "최초 원액 용량 (µL)": None,
                "원액 누적 사용량 (µL)": None,
                "원액 잔량 (µL)": None,
                "희석액(1/100) 튜브 수 (n)": None,
                "준비 상태": "미보유",
                "재고 점검": "—",
                "비고": "—",
                "매칭 점수": item["매칭 점수"],
            })
            continue

        for match in matches:
            readiness, check = resource_readiness(match)
            rows.append({
                "입력 표적": target_label,
                "질환군": item.get("system", "기타"),
                "병원체 유형": item.get("kind", "미분류"),
                "검증 구분": item.get("검증 구분", "특이도"),
                "우선순위": item.get("우선순위", "참고"),
                "추천 미생물": item["organism"],
                "보유 여부": "보유",
                "관리번호": _match_value(match, "inventory_id") or "—",
                "사내 자원명": _match_value(match, "inventory_name") or "—",
                "Cat no.": _match_value(match, "catalog_no") or "—",
                "구매일": _match_value(match, "purchase_date") or "—",
                "최초 원액 용량 (µL)": _display_provided_number(_match_value(match, "initial_volume_ul")),
                "원액 누적 사용량 (µL)": _display_provided_number(_match_value(match, "cumulative_use_ul")),
                "원액 잔량 (µL)": _display_provided_number(_match_value(match, "remaining_volume_ul")),
                "희석액(1/100) 튜브 수 (n)": _display_provided_number(_match_value(match, "dilution_tubes")),
                "준비 상태": readiness,
                "재고 점검": check,
                "비고": _match_value(match, "notes") or "—",
                "매칭 점수": _match_value(match, "score", 0.0),
            })
    return rows
