"""qPCR 교차반응 검토용 기본 후보 데이터.

아래 목록은 시험 설계를 시작하기 위한 참고 패널이며, 특정 키트의 성능을
보증하거나 규제기관의 필수 패널을 대체하지 않는다.
"""

from __future__ import annotations

import re


TARGET_ALIASES = {
    "stec": ("stec", "ehec", "stx1", "stx2", "shiga toxin", "시가독소", "장출혈성 대장균",
             "escherichia coli o157", "e. coli o157", "e coli o157"),
    "shigella": ("shigella", "ipah", "이질균", "세균성 이질"),
    "salmonella": ("salmonella", "inva", "ttr", "살모넬라"),
    "campylobacter": ("campylobacter", "campylobacter jejuni", "c. jejuni", "c jejuni",
                       "mapa", "cadf", "캄필로박터"),
    "c_difficile": ("clostridioides difficile", "clostridium difficile", "c. difficile", "c difficile",
                     "tcda", "tcdb", "cdiff", "클로스트리디오이데스"),
    "listeria": ("listeria monocytogenes", "l. monocytogenes", "l monocytogenes",
                  "listeria", "hlya", "prfa", "iap", "리스테리아 모노사이토제네스",
                  "리스테리아"),
    "norovirus": ("norovirus", "noro", "orf1", "orf2", "노로바이러스"),
    "rotavirus": ("rotavirus", "nsp3", "vp6", "로타바이러스"),
    "sars_cov_2": ("sars-cov-2", "sars cov 2", "covid", "2019-ncov", "rdrp", "코로나19"),
    "influenza": ("influenza", "matrix gene", "m gene", "인플루엔자", "독감"),
    "rsv": ("respiratory syncytial", "rsv", "호흡기세포융합"),
    "pertussis": ("bordetella pertussis", "b. pertussis", "b pertussis", "is481", "ptxs1", "백일해"),
    "m_pneumoniae": ("mycoplasma pneumoniae", "m. pneumoniae", "m pneumoniae",
                      "p1", "마이코플라스마 폐렴"),
    "malaria": ("plasmodium", "18s rrna", "plasmodium falciparum",
                "p. falciparum", "plasmodium vivax", "p. vivax", "plasmodium malariae",
                "p. malariae", "plasmodium ovale", "p. ovale", "plasmodium knowlesi", "p. knowlesi"),
    "babesia": ("babesia", "babesiosis", "바베시아", "바베시아증", "babesia microti",
                "b. microti", "babesia divergens", "b. divergens"),
}

TARGET_LABELS = {
    "stec": "STEC/EHEC", "shigella": "Shigella", "salmonella": "Salmonella",
    "campylobacter": "Campylobacter", "c_difficile": "C. difficile",
    "listeria": "Listeria monocytogenes",
    "norovirus": "Norovirus", "rotavirus": "Rotavirus", "sars_cov_2": "SARS-CoV-2",
    "influenza": "Influenza", "rsv": "RSV", "pertussis": "B. pertussis",
    "m_pneumoniae": "M. pneumoniae",
    "malaria": "Malaria/Plasmodium", "babesia": "Babesia",
}

TARGET_SYSTEMS = {
    "stec": "장관계", "shigella": "장관계", "salmonella": "장관계",
    "campylobacter": "장관계", "c_difficile": "장관계",
    "listeria": "장관계",
    "norovirus": "장관계", "rotavirus": "장관계",
    "sars_cov_2": "호흡기계", "influenza": "호흡기계", "rsv": "호흡기계",
    "pertussis": "호흡기계", "m_pneumoniae": "호흡기계",
    "malaria": "혈액매개", "babesia": "혈액매개",
}

if not (set(TARGET_ALIASES) == set(TARGET_LABELS) == set(TARGET_SYSTEMS)):
    raise RuntimeError("타겟 별칭, 표시명, 증후군 매핑의 키가 일치하지 않습니다.")


def row(system, kind, organism, relation, basis, targets, aliases=()):
    if relation == "동시감염균":
        relation = "동시감염 병원체"
    return {"system": system, "kind": kind, "organism": organism, "relation": relation,
            "basis": basis, "targets": tuple(targets), "aliases": tuple(aliases)}


CROSS_REACTIVITY_ROWS = [
    row("장관계", "세균", "Escherichia albertii", "근연종", "Escherichia 속 및 병원성 유전자 표적의 특이성 확인", ["stec"], ["E. albertii"]),
    row("장관계", "세균", "Escherichia fergusonii", "근연종", "Escherichia 속 내 비표적 종 구별 확인", ["stec"], ["E. fergusonii"]),
    row("장관계", "세균", "Shigella dysenteriae", "근연종", "Shigella/EIEC 계열 표적의 종간 반응 확인", ["shigella", "stec"], ["S. dysenteriae"]),
    row("장관계", "세균", "Shigella flexneri", "근연종", "Shigella 종군 내 포괄성과 특이성 확인", ["shigella"], ["S. flexneri"]),
    row("장관계", "세균", "Shigella sonnei", "근연종", "Shigella 종군 내 포괄성과 특이성 확인", ["shigella"], ["S. sonnei"]),
    row("장관계", "세균", "Salmonella bongori", "근연종", "S. enterica와의 종 수준 구별 확인", ["salmonella"], ["S. bongori"]),
    row("장관계", "세균", "Campylobacter coli", "근연종", "C. jejuni 표적의 근연 Campylobacter 반응 확인", ["campylobacter"], ["C. coli"]),
    row("장관계", "세균", "Campylobacter lari", "근연종", "Campylobacter 종군 내 비표적 반응 확인", ["campylobacter"], ["C. lari"]),
    row("장관계", "세균", "Clostridium perfringens", "근연종", "근연 혐기성 세균의 비특이 반응 확인", ["c_difficile"], ["C. perfringens"]),
    row("장관계", "세균", "Listeria innocua", "근연종", "L. monocytogenes 표적의 근연 Listeria 종 비특이 반응 확인", ["listeria"], ["L. innocua"]),
    row("장관계", "세균", "Listeria ivanovii", "근연종", "Listeria 속 내 종 수준 특이성 확인", ["listeria"], ["L. ivanovii"]),
    row("장관계", "세균", "Listeria seeligeri", "근연종", "Listeria 속 내 종 수준 특이성 확인", ["listeria"], ["L. seeligeri"]),
    row("장관계", "세균", "Listeria welshimeri", "근연종", "Listeria 속 내 종 수준 특이성 확인", ["listeria"], ["L. welshimeri"]),
    row("장관계", "세균", "Salmonella enterica", "동시감염균", "급성 장관감염에서 함께 감별할 주요 병원체", ["stec", "shigella", "campylobacter", "c_difficile", "listeria"], ["S. enterica"]),
    row("장관계", "세균", "Campylobacter jejuni", "동시감염균", "세균성 장염의 주요 동시감염·감별 후보", ["stec", "shigella", "salmonella", "c_difficile", "listeria"], ["C. jejuni"]),
    row("장관계", "세균", "Yersinia enterocolitica", "동시감염균", "설사 검체에서 임상 증상이 중첩되는 감별 후보", ["stec", "shigella", "salmonella", "campylobacter", "listeria"], ["Y. enterocolitica"]),
    row("장관계", "세균", "Vibrio parahaemolyticus", "동시감염균", "식품매개 장염의 동시감염·감별 후보", ["stec", "shigella", "salmonella", "campylobacter"], ["V. parahaemolyticus"]),
    row("장관계", "세균", "Aeromonas hydrophila", "동시감염균", "수인성 설사 검체의 감별 후보", ["stec", "shigella", "salmonella"], ["A. hydrophila"]),
    row("장관계", "세균", "Plesiomonas shigelloides", "동시감염균", "장관감염에서 Shigella와 임상적으로 중첩 가능한 후보", ["shigella", "stec"], ["P. shigelloides"]),
    row("장관계", "바이러스", "Norovirus GI", "근연종", "Norovirus 유전자군 간 포괄성과 교차반응 확인", ["norovirus"], ["Norwalk virus GI"]),
    row("장관계", "바이러스", "Norovirus GII", "근연종", "Norovirus 유전자군 간 포괄성과 교차반응 확인", ["norovirus"], ["Norwalk virus GII"]),
    row("장관계", "바이러스", "Sapovirus", "근연종", "Caliciviridae 내 비표적 반응 확인", ["norovirus"]),
    row("장관계", "바이러스", "Rotavirus B", "근연종", "Rotavirus A 표적의 종간 특이성 확인", ["rotavirus"]),
    row("장관계", "바이러스", "Rotavirus C", "근연종", "Rotavirus A 표적의 종간 특이성 확인", ["rotavirus"]),
    row("장관계", "바이러스", "Rotavirus A", "동시감염균", "바이러스성 장관염의 주요 동시감염 후보", ["norovirus"]),
    row("장관계", "바이러스", "Human astrovirus", "동시감염균", "바이러스성 장관감염 감별 후보", ["norovirus", "rotavirus"], ["Astrovirus"]),
    row("장관계", "바이러스", "Human adenovirus F40/41", "동시감염균", "장관형 adenovirus 감별 후보", ["norovirus", "rotavirus"], ["Enteric adenovirus 40", "Enteric adenovirus 41"]),
    row("호흡기계", "세균", "Bordetella parapertussis", "근연종", "Bordetella 표적 및 IS 계열 비특이 반응 확인", ["pertussis"], ["B. parapertussis"]),
    row("호흡기계", "세균", "Bordetella holmesii", "근연종", "IS481 기반 검사에서 중요한 비표적 후보", ["pertussis"], ["B. holmesii"]),
    row("호흡기계", "세균", "Bordetella bronchiseptica", "근연종", "Bordetella 속 내 특이성 확인", ["pertussis"], ["B. bronchiseptica"]),
    row("호흡기계", "세균", "Mycoplasma genitalium", "근연종", "Mycoplasma 속 내 표적 특이성 확인", ["m_pneumoniae"], ["M. genitalium"]),
    row("호흡기계", "세균", "Streptococcus mitis", "근연종", "S. pneumoniae와 유전적으로 가까운 구강 연쇄상구균 감별", ["m_pneumoniae", "pertussis"], ["S. mitis"]),
    row("호흡기계", "세균", "Haemophilus influenzae", "동시감염균", "호흡기 검체의 주요 세균성 동시감염 후보", ["pertussis", "m_pneumoniae", "sars_cov_2", "influenza", "rsv"], ["H. influenzae"]),
    row("호흡기계", "세균", "Streptococcus pneumoniae", "동시감염균", "호흡기 감염의 대표 세균성 동시감염 후보", ["pertussis", "m_pneumoniae", "sars_cov_2", "influenza", "rsv"], ["S. pneumoniae"]),
    row("호흡기계", "세균", "Moraxella catarrhalis", "동시감염균", "상·하기도 감염 감별 후보", ["pertussis", "m_pneumoniae", "influenza", "rsv"], ["M. catarrhalis"]),
    row("호흡기계", "세균", "Staphylococcus aureus", "동시감염균", "바이러스성 호흡기 감염 후 세균성 동시감염 후보", ["sars_cov_2", "influenza", "rsv"], ["S. aureus"]),
    row("호흡기계", "바이러스", "SARS-CoV-1", "근연종", "Sarbecovirus 공통 부위 분석 특이성 확인", ["sars_cov_2"], ["SARS coronavirus"]),
    row("호흡기계", "바이러스", "MERS-CoV", "근연종", "Betacoronavirus 내 비표적 반응 확인", ["sars_cov_2"], ["Middle East respiratory syndrome coronavirus"]),
    row("호흡기계", "바이러스", "Human coronavirus OC43", "근연종", "계절성 coronavirus 비표적 반응 확인", ["sars_cov_2"], ["HCoV-OC43"]),
    row("호흡기계", "바이러스", "Human coronavirus 229E", "근연종", "계절성 coronavirus 비표적 반응 확인", ["sars_cov_2"], ["HCoV-229E"]),
    row("호흡기계", "바이러스", "Influenza B virus", "근연종", "Influenza A/B 또는 공통 matrix 표적 구별 확인", ["influenza"], ["Flu B"]),
    row("호흡기계", "바이러스", "Respiratory syncytial virus A", "근연종", "RSV 아형 간 포괄성과 특이성 확인", ["rsv"], ["RSV A"]),
    row("호흡기계", "바이러스", "Respiratory syncytial virus B", "근연종", "RSV 아형 간 포괄성과 특이성 확인", ["rsv"], ["RSV B"]),
    row("호흡기계", "바이러스", "Influenza A virus", "동시감염균", "호흡기 다중감염 패널의 주요 감별 후보", ["sars_cov_2", "rsv"], ["Flu A"]),
    row("호흡기계", "바이러스", "Human metapneumovirus", "동시감염균", "RSV와 임상 양상이 중첩되는 감별 후보", ["rsv", "sars_cov_2", "influenza"], ["hMPV"]),
    row("호흡기계", "바이러스", "Human parainfluenza virus 1", "동시감염균", "급성 호흡기 감염 감별 후보", ["sars_cov_2", "influenza", "rsv"], ["HPIV-1"]),
    row("호흡기계", "바이러스", "Human rhinovirus", "동시감염균", "상기도 감염의 흔한 동시 검출 후보", ["sars_cov_2", "influenza", "rsv"], ["Rhinovirus"]),
    row("호흡기계", "바이러스", "Human adenovirus", "동시감염균", "호흡기 증후군 패널의 감별 후보", ["sars_cov_2", "influenza", "rsv"], ["Adenovirus"]),
    row("혈액매개", "기생충", "Plasmodium falciparum", "근연종", "사람 말라리아 원충 종간 포괄성과 종 특이성 확인", ["malaria"], ["P. falciparum"]),
    row("혈액매개", "기생충", "Plasmodium vivax", "근연종", "사람 말라리아 원충 종간 포괄성과 종 특이성 확인", ["malaria"], ["P. vivax"]),
    row("혈액매개", "기생충", "Plasmodium malariae", "근연종", "사람 말라리아 원충 종간 포괄성과 종 특이성 확인", ["malaria"], ["P. malariae"]),
    row("혈액매개", "기생충", "Plasmodium ovale", "근연종", "사람 말라리아 원충 종간 포괄성과 종 특이성 확인", ["malaria"], ["P. ovale"]),
    row("혈액매개", "기생충", "Plasmodium knowlesi", "근연종", "사람 말라리아 원충 종간 포괄성과 종 특이성 확인", ["malaria"], ["P. knowlesi"]),
    row("혈액매개", "기생충", "Babesia microti", "감별 병원체", "적혈구 내 원충으로 Plasmodium과 감별 및 비특이 반응 확인", ["babesia"], ["B. microti"]),
    row("혈액매개", "기생충", "Babesia divergens", "감별 병원체", "적혈구 내 원충으로 Plasmodium과 감별 및 비특이 반응 확인", ["babesia"], ["B. divergens"]),
]

DISEASE_QUERY_TERMS = (
    "장관계 감염증", "장관 감염", "장염", "설사 질환", "gastroenteritis",
    "호흡기계 감염증", "호흡기계 감염", "호흡기 감염증", "호흡기 감염", "폐렴", "respiratory infection",
    "혈액매개 감염", "bloodborne infection", "말라리아", "malaria",
)

SCOPE_PRIORITY = {
    "사용자 입력": 6,
    "표적 직접 연관": 5,
    "직접 검색": 4,
    "질환군 전체": 3,
    "증후군 확장": 2,
    "기본 패널": 1,
}


def _contains_term(text: str, term: str) -> bool:
    """영문 약어는 단어 경계로 찾아 짧은 표적명(p1, ari 등)의 오인을 막는다."""
    lowered = term.lower()
    if re.search(r"[a-z0-9]", lowered):
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(lowered)}(?![a-z0-9])", text))
    return lowered in text


def _catalog_matches(text: str):
    """등록 후보의 정식명·별칭을 타겟 검색어로도 활용한다."""
    matches = []
    for item in CROSS_REACTIVITY_ROWS:
        names = (item["organism"], *item["aliases"])
        if any(_contains_term(text, name) for name in names):
            matches.append(item)
    return matches


def is_disease_query(query: str) -> bool:
    """질환명만 입력한 경우를 식별해 검출 타겟 검색과 분리한다."""
    text = (query or "").strip().lower()
    return bool(text) and any(_contains_term(text, term) for term in DISEASE_QUERY_TERMS)


def _panel_interpretation(prefix: str, systems: set[str]) -> str:
    panel_kinds = [
        kind for kind in ("세균", "바이러스", "기생충")
        if any(item["system"] in systems and item["kind"] == kind for item in CROSS_REACTIVITY_ROWS)
    ]
    return f"{prefix} · 포괄 패널: {'/'.join(sorted(systems))} " + "+".join(panel_kinds)


def select_cross_reactivity_rows(query: str):
    """유전자·균주·병원체 입력을 해석해 (후보 목록, 해석 문구)를 반환한다."""
    text = (query or "").strip().lower()
    if is_disease_query(query):
        return [], "질환명은 검색 대상이 아닙니다. 실제 균주·병원체명 또는 표적 유전자를 입력해 주세요."
    target_ids = {key for key, aliases in TARGET_ALIASES.items() if any(_contains_term(text, alias) for alias in aliases)}

    if target_ids:
        target_systems = {TARGET_SYSTEMS[key] for key in target_ids}
        direct = [item for item in CROSS_REACTIVITY_ROWS if target_ids.intersection(item["targets"])]
        expanded = [item for item in CROSS_REACTIVITY_ROWS
                    if item["system"] in target_systems and not target_ids.intersection(item["targets"])]
        rows = []
        for item in direct:
            copied = dict(item)
            copied["scope"] = "표적 직접 연관"
            rows.append(copied)
        for item in expanded:
            copied = dict(item)
            copied["scope"] = "증후군 확장"
            copied["relation"] = "증후군 감별 병원체"
            copied["basis"] = f"{item['system']} 감염 증후군에서 표적 외 동시감염·감별을 포괄하기 위한 확장 후보"
            rows.append(copied)
        labels = ", ".join(TARGET_LABELS[key] for key in sorted(target_ids))
        interpretation = _panel_interpretation(f"표적: {labels}", target_systems)
    else:
        direct = _catalog_matches(text) if text else []
        if direct:
            direct_keys = {(item["system"], item["kind"], item["organism"]) for item in direct}
            direct_systems = {item["system"] for item in direct}
            rows = []
            for item in CROSS_REACTIVITY_ROWS:
                if item["system"] not in direct_systems:
                    continue
                copied = dict(item)
                key = (item["system"], item["kind"], item["organism"])
                if key in direct_keys:
                    copied["scope"] = "직접 검색"
                else:
                    copied["scope"] = "증후군 확장"
                    copied["relation"] = "증후군 감별 병원체"
                    copied["basis"] = f"{item['system']} 감염 증후군에서 함께 검토할 확장 후보"
                rows.append(copied)
            names = ", ".join(dict.fromkeys(item["organism"] for item in direct))
            interpretation = _panel_interpretation(f"병원체: {names}", direct_systems)
        elif text:
            rows = [{
                "system": "기타",
                "kind": "미분류",
                "organism": (query or "").strip(),
                "relation": "사용자 입력 병원체",
                "basis": "등록 패널에 없는 입력입니다. 사내 자원 대조는 수행하며 분류와 교차반응 후보는 검토 후 추가해야 합니다.",
                "targets": (),
                "aliases": (),
                "scope": "사용자 입력",
            }]
            interpretation = f"사용자 입력 병원체: {(query or '').strip()} · 자동 분류 필요"
        else:
            rows = [{**item, "scope": "기본 패널"} for item in CROSS_REACTIVITY_ROWS]
            interpretation = "전체 기본 패널"

    seen, unique = set(), []
    for item in rows:
        key = (item["system"], item["kind"], item["organism"], item["relation"])
        if key not in seen:
            seen.add(key)
            unique.append(dict(item))
    return unique, interpretation


def select_cross_reactivity_rows_for_targets(target_queries):
    """여러 입력 타겟을 개별 해석하고 미생물별 관련 입력 타겟을 병합한다."""
    targets = []
    for query in target_queries:
        cleaned = (query or "").strip()
        if cleaned and cleaned.casefold() not in {item.casefold() for item in targets}:
            targets.append(cleaned)

    merged = {}
    interpretations = []
    unrecognized = []
    for target in targets:
        rows, interpretation = select_cross_reactivity_rows(target)
        if any(item.get("scope") == "사용자 입력" for item in rows):
            unrecognized.append(target)
        interpretations.append(f"{target}: {interpretation}")
        for row_item in rows:
            key = (row_item["system"], row_item["kind"], row_item["organism"])
            if key not in merged:
                merged[key] = {**row_item, "input_targets": [target]}
                continue
            existing = merged[key]
            existing["input_targets"].append(target)
            if SCOPE_PRIORITY.get(row_item.get("scope", ""), 0) > SCOPE_PRIORITY.get(existing.get("scope", ""), 0):
                related_targets = existing["input_targets"]
                existing.update(row_item)
                existing["input_targets"] = related_targets

    output = []
    for item in merged.values():
        item["input_targets"] = tuple(dict.fromkeys(item["input_targets"]))
        output.append(item)
    interpretation = " | ".join(interpretations) if interpretations else "인식된 타겟 없음"
    return output, interpretation, unrecognized
