"""사내 보유 자원 파일을 읽고 미생물명을 유사 매칭하는 기능."""

from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz


NAME_HINTS = {"표준물질 균주명", "균주명", "미생물명", "표준물질명", "제품명", "organism",
              "microorganism", "microbe", "sample name", "strain", "scientific name"}
ID_HINTS = {"관리번호", "id", "sample id", "자원번호", "resource id"}
CATALOG_HINTS = {"cat no.", "cat no", "catalog no", "catalog number", "카탈로그번호", "제품번호"}
PURCHASE_DATE_HINTS = {"구매일", "구입일", "purchase date"}
INITIAL_VOLUME_HINTS = {"최초 원액 용량", "initial stock volume"}
CUMULATIVE_USE_HINTS = {"원액 누적 사용량", "cumulative stock use", "cumulative use"}
REMAINING_VOLUME_HINTS = {"원액 잔량", "remaining stock", "stock remaining"}
DILUTION_TUBE_HINTS = {"희석액(1/100) 튜브 수", "희석액(1/100) 튜브", "희석액 튜브 수", "dilution tube"}
NOTES_HINTS = {"비고", "notes", "note", "remarks"}

RESOURCE_FIELD_HINTS = (
    PURCHASE_DATE_HINTS | INITIAL_VOLUME_HINTS | CUMULATIVE_USE_HINTS
    | REMAINING_VOLUME_HINTS | DILUTION_TUBE_HINTS | NOTES_HINTS
)

CANONICAL_ALIASES = {
    "escherichia coli": {"e coli", "e. coli", "escherichia coli"},
    "clostridioides difficile": {"clostridioides difficile", "clostridium difficile", "c difficile", "c. difficile", "cdiff"},
    "sars cov 2": {"sars cov 2", "sars-cov-2", "2019 ncov", "2019-ncov", "covid 19 virus"},
    "respiratory syncytial virus": {"respiratory syncytial virus", "rsv"},
    "human metapneumovirus": {"human metapneumovirus", "hmpv"},
    "influenza a virus": {"influenza a virus", "influenza a", "flu a"},
    "influenza b virus": {"influenza b virus", "influenza b", "flu b"},
}


def _basic_normalize(value) -> str:
    text = unicodedata.normalize("NFKC", str(value)).lower().strip()
    text = re.sub(r"[^a-z0-9가-힣]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


NORMALIZED_ALIAS_TO_CANONICAL = {
    _basic_normalize(alias): canonical
    for canonical, aliases in CANONICAL_ALIASES.items()
    for alias in {*aliases, canonical}
}


def normalize_name(value) -> str:
    if value is None or pd.isna(value):
        return ""
    text = _basic_normalize(value)
    text = re.sub(r"\b(genomic|purified|synthetic|inactivated|whole|dna|rna|control|standard|strain|isolate)\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return NORMALIZED_ALIAS_TO_CANONICAL.get(text, text)


def _header(value) -> str:
    return "" if value is None or pd.isna(value) else re.sub(r"\s+", " ", str(value).replace("\n", " ").strip().lower())


def _matches_hint(column: str, hints: set[str]) -> bool:
    for hint in hints:
        if column == hint:
            return True
        # ``id``처럼 짧은 힌트를 단순 부분 문자열로 찾으면 ``validity`` 같은
        # 전혀 다른 열이 관리번호 열로 오인된다.
        if len(hint) <= 2:
            if re.search(rf"(?<![a-z0-9가-힣]){re.escape(hint)}(?![a-z0-9가-힣])", column):
                return True
        elif hint in column:
            return True
    return False


def _detect_header(raw: pd.DataFrame) -> int:
    best_row, best_score = 0, -1
    hints = NAME_HINTS | ID_HINTS | CATALOG_HINTS | RESOURCE_FIELD_HINTS
    for index in range(min(25, len(raw))):
        score = sum(_matches_hint(_header(value), hints) for value in raw.iloc[index] if pd.notna(value))
        if score > best_score:
            best_row, best_score = index, score
    return best_row


def _unique_headers(values) -> list[str]:
    output, used = [], set()
    for index, value in enumerate(values):
        name = _header(value) or f"unnamed_{index}"
        while name in used:
            name += f"_{index}"
        used.add(name)
        output.append(name)
    return output


def _read_csv(data: bytes) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
        try:
            return pd.read_csv(io.BytesIO(data), header=None, dtype=object, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("CSV 문자 인코딩을 읽을 수 없습니다. UTF-8 또는 CP949로 저장해 주세요.")


def _clean_cell(value) -> str:
    """셀을 식별자용 문자열로 변환하되 NaN과 정수형 실수 표기를 정리한다."""
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _first_matching_column(columns, hints: set[str]) -> str | None:
    return next((column for column in columns if _matches_hint(column, hints)), None)


def _is_plausible_name(value: str) -> bool:
    """URL·숫자만 있는 값 등 명백히 미생물명이 아닌 행을 제외한다."""
    text = value.strip()
    if (
        not text
        or text.startswith(("=", "+", "-", "@"))
        or re.match(r"^(?:https?://|www\.)", text, flags=re.IGNORECASE)
    ):
        return False
    if re.fullmatch(r"[\d\W_]+", text):
        return False
    return bool(normalize_name(text))


def excel_safe_value(value):
    """다운로드 Excel에서 업로드 문자열이 수식으로 실행되지 않게 한다."""
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def read_inventory(uploaded_file) -> pd.DataFrame:
    """CSV 또는 XLSX의 모든 시트에서 보유 자원 레코드를 추출한다."""
    name = getattr(uploaded_file, "name", "inventory.xlsx")
    suffix = Path(name).suffix.lower()
    data = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
    if suffix == ".csv":
        sheets = {"CSV": _read_csv(data)}
    elif suffix in {".xlsx", ".xlsm"}:
        sheets = pd.read_excel(io.BytesIO(data), sheet_name=None, header=None, dtype=object, engine="openpyxl")
    else:
        raise ValueError("지원 형식은 CSV, XLSX, XLSM입니다.")

    records = []
    for sheet_name, raw in sheets.items():
        if raw.empty:
            continue
        header_index = _detect_header(raw)
        frame = raw.iloc[header_index + 1:].copy()
        frame.columns = _unique_headers(raw.iloc[header_index])
        frame = frame.dropna(how="all")
        name_columns = [column for column in frame.columns if _matches_hint(column, NAME_HINTS)]
        if not name_columns:
            continue
        id_columns = [column for column in frame.columns if _matches_hint(column, ID_HINTS)]
        catalog_columns = [column for column in frame.columns if _matches_hint(column, CATALOG_HINTS)]
        purchase_date_column = _first_matching_column(frame.columns, PURCHASE_DATE_HINTS)
        initial_volume_column = _first_matching_column(frame.columns, INITIAL_VOLUME_HINTS)
        cumulative_use_column = _first_matching_column(frame.columns, CUMULATIVE_USE_HINTS)
        remaining_volume_column = _first_matching_column(frame.columns, REMAINING_VOLUME_HINTS)
        dilution_tube_column = _first_matching_column(frame.columns, DILUTION_TUBE_HINTS)
        notes_column = _first_matching_column(frame.columns, NOTES_HINTS)
        if not id_columns:
            # 일부 사내 양식은 관리번호(Z001, V001 등)가 들어 있는 첫 열의 헤더가
            # 병합/누락되어 있다. 값 패턴이 충분히 일관되면 관리번호 열로 인식한다.
            for column in frame.columns:
                sample = [str(value).strip() for value in frame[column].dropna().head(40)]
                if sample:
                    matched = sum(bool(re.fullmatch(r"[A-Za-z]{1,5}[-_]?\d{2,}", value)) for value in sample)
                    if matched / len(sample) >= 0.7:
                        id_columns = [column]
                        break
        for _, record in frame.iterrows():
            candidates = [_clean_cell(record[column]) for column in name_columns
                          if _clean_cell(record.get(column)) and _is_plausible_name(_clean_cell(record[column]))]
            if not candidates:
                continue
            records.append({
                "sheet": str(sheet_name), "inventory_name": candidates[0],
                "candidate_names": tuple(dict.fromkeys(candidates)),
                "inventory_id": _clean_cell(record.get(id_columns[0])) if id_columns else "",
                "catalog_no": _clean_cell(record.get(catalog_columns[0])) if catalog_columns else "",
                "purchase_date": _clean_cell(record.get(purchase_date_column)) if purchase_date_column else "",
                "initial_volume_ul": _clean_cell(record.get(initial_volume_column)) if initial_volume_column else "",
                "cumulative_use_ul": _clean_cell(record.get(cumulative_use_column)) if cumulative_use_column else "",
                "remaining_volume_ul": _clean_cell(record.get(remaining_volume_column)) if remaining_volume_column else "",
                "dilution_tubes": _clean_cell(record.get(dilution_tube_column)) if dilution_tube_column else "",
                "notes": _clean_cell(record.get(notes_column)) if notes_column else "",
            })
    if not records:
        raise ValueError("미생물명 열을 찾지 못했습니다. '균주명', '미생물명' 또는 'Organism' 열을 포함해 주세요.")
    return pd.DataFrame(records)


def _expand_abbreviation(candidate: str, target: str) -> str:
    parts, target_parts = candidate.split(), target.split()
    if len(parts) >= 2 and len(parts[0]) == 1 and len(target_parts) >= 2 and parts[0] == target_parts[0][0]:
        return " ".join([target_parts[0], *parts[1:]])
    return candidate


def _has_identity_conflict(target: str, candidate: str) -> bool:
    """서로 다른 종·형·아형을 높은 철자 유사도로 합치는 오탐을 막는다."""
    left, right = target.split(), candidate.split()
    if not left or not right:
        return False

    # 이명법 형태의 세균명은 종소명이 다르거나 속명이 전혀 다르면 별개로
    # 취급한다. 속명의 작은 철자 오류(Moraxella/Morexella)는 허용한다.
    non_binomial_stems = {"human", "influenza", "norovirus", "respiratory", "rotavirus", "sars"}
    if (
        len(left) == 2
        and len(right) >= 2
        and left[0] not in non_binomial_stems
        and len(left[1]) >= 3
        and len(right[1]) >= 3
    ):
        if left[1] != right[1] or fuzz.ratio(left[0], right[0]) < 85:
            return True

    def classifier(token: str) -> bool:
        return bool(
            re.fullmatch(r"[a-z]", token)
            or re.fullmatch(r"g?[ivx]{1,5}", token)
            or (re.search(r"\d", token) and len(token) <= 8)
        )

    def classifier_key(token: str) -> str:
        return token[1:] if re.fullmatch(r"f\d+", token) else token

    target_classes = {classifier_key(token) for token in left if classifier(token)}
    candidate_classes = {classifier_key(token) for token in right if classifier(token)}
    # 구체 아형을 요구하는 후보는 이름에 아형이 없거나 서로 다르면 보수적으로
    # 불일치 처리한다. 반대로 상위 표적(Human adenovirus 등)은 하위 type을 허용한다.
    aligned_classifier_conflict = any(
        classifier_key(a) != classifier_key(b) and classifier(a) and classifier(b)
        for a, b in zip(left, right)
    )
    if (len(target_classes) == 1 and aligned_classifier_conflict) or (
        target_classes and (not candidate_classes or target_classes.isdisjoint(candidate_classes))
    ):
        return True
    return False


def _has_meaningful_overlap(target: str, candidate: str) -> bool:
    weak = {"bacterium", "dna", "from", "human", "isolate", "rna", "species", "subsp", "type", "virus"}
    left, right = target.split(), candidate.split()
    if (
        len(left) == 2
        and len(right) >= 2
        and len(left[1]) >= 3
        and len(right[1]) >= 3
        and left[1] == right[1]
        and fuzz.ratio(left[0], right[0]) >= 85
    ):
        return True

    def is_classifier(token: str) -> bool:
        return bool(
            re.fullmatch(r"[a-z]", token)
            or re.fullmatch(r"g?[ivx]{1,5}", token)
            or (re.search(r"\d", token) and len(token) <= 8)
        )

    target_tokens = {token for token in left if token not in weak and not is_classifier(token)}
    candidate_tokens = {token for token in right if token not in weak and not is_classifier(token)}
    if not target_tokens:
        return False
    overlap = target_tokens.intersection(candidate_tokens)
    required = 1 if len(target_tokens) == 1 else 2
    return len(overlap) >= required


def similarity_score(target_name: str, inventory_name: str, aliases=()) -> tuple[float, str]:
    targets = [normalize_name(target_name), *(normalize_name(alias) for alias in aliases)]
    candidate = normalize_name(inventory_name)
    targets = [target for target in targets if target]
    if not candidate or not targets:
        return 0.0, "불일치"
    best, method = 0.0, "RapidFuzz"
    for target in targets:
        comparison_target = _expand_abbreviation(target, candidate)
        expanded = _expand_abbreviation(candidate, comparison_target)
        if expanded == comparison_target:
            return 100.0, "정규화 일치"
        if _has_identity_conflict(comparison_target, expanded):
            # UI의 최저 임계값(70)보다 낮게 제한해 사용자가 임계값을 낮춰도
            # 명백히 다른 종·아형이 보유로 판정되지 않게 한다.
            score = min(
                float(fuzz.WRatio(comparison_target, expanded)),
                float(fuzz.token_set_ratio(comparison_target, expanded)),
                69.0,
            )
            if score > best:
                best, method = score, "종·아형 불일치"
            continue
        def classification_keys(text: str) -> set[str]:
            keys = set()
            for token in text.split():
                if (
                    re.fullmatch(r"[a-z]", token)
                    or re.fullmatch(r"g?[ivx]{1,5}", token)
                    or (re.search(r"\d", token) and len(token) <= 8)
                ):
                    keys.add(token[1:] if re.fullmatch(r"f\d+", token) else token)
            return keys

        if (
            classification_keys(comparison_target).intersection(classification_keys(expanded))
            and _has_meaningful_overlap(comparison_target, expanded)
        ):
            best, method = max(best, 97.0), "형 일치"
        if len(comparison_target.split()) >= 2 and (
            expanded.startswith(comparison_target + " ") or comparison_target.startswith(expanded + " ")
        ):
            best, method = max(best, 97.0), "학명 포함"
        score = max(
            float(fuzz.WRatio(comparison_target, expanded)),
            float(fuzz.token_set_ratio(comparison_target, expanded)),
        )
        if not _has_meaningful_overlap(comparison_target, expanded):
            score = min(score, 69.0)
            candidate_method = "핵심 명칭 불일치"
        else:
            candidate_method = "RapidFuzz"
        if score > best:
            best, method = score, candidate_method
    return round(best, 1), method


@dataclass(frozen=True)
class MatchResult:
    owned: bool
    score: float
    method: str
    inventory_name: str = ""
    inventory_id: str = ""
    catalog_no: str = ""
    sheet: str = ""
    purchase_date: str = ""
    initial_volume_ul: str = ""
    cumulative_use_ul: str = ""
    remaining_volume_ul: str = ""
    dilution_tubes: str = ""
    notes: str = ""


def find_matches(
    target_name: str,
    aliases,
    inventory: pd.DataFrame | None,
    threshold: int = 86,
) -> tuple[list[MatchResult], MatchResult]:
    """모든 임계값 이상 매치와 전체 최적 매치를 한 번의 재고 순회로 반환한다."""
    if inventory is None or inventory.empty:
        return [], MatchResult(False, 0.0, "재고 파일 없음")

    best = MatchResult(False, 0.0, "불일치")
    matches = []
    seen = set()
    for _, record in inventory.iterrows():
        best_score, best_method = 0.0, "불일치"
        for candidate in record["candidate_names"]:
            score, method = similarity_score(target_name, candidate, aliases)
            if score > best_score:
                best_score, best_method = score, method
        inventory_id = str(record.get("inventory_id", ""))
        inventory_name = str(record.get("inventory_name", ""))
        catalog_no = str(record.get("catalog_no", ""))
        sheet = str(record.get("sheet", ""))
        result = MatchResult(
            best_score >= threshold, best_score, best_method,
            inventory_name, inventory_id, catalog_no, sheet,
            str(record.get("purchase_date", "")),
            str(record.get("initial_volume_ul", "")),
            str(record.get("cumulative_use_ul", "")),
            str(record.get("remaining_volume_ul", "")),
            str(record.get("dilution_tubes", "")),
            str(record.get("notes", "")),
        )
        if best_score > best.score:
            best = result
        if best_score < threshold:
            continue
        key = (inventory_id, inventory_name, catalog_no, sheet)
        if key in seen:
            continue
        seen.add(key)
        matches.append(result)
    matches.sort(key=lambda item: (-item.score, item.inventory_id, item.inventory_name))
    return matches, best


def find_best_match(target_name: str, aliases, inventory: pd.DataFrame | None, threshold: int = 86) -> MatchResult:
    return find_matches(target_name, aliases, inventory, threshold)[1]


def find_all_matches(target_name: str, aliases, inventory: pd.DataFrame | None, threshold: int = 86) -> list[MatchResult]:
    """임계값 이상인 모든 사내 자원 레코드를 반환한다."""
    return find_matches(target_name, aliases, inventory, threshold)[0]
