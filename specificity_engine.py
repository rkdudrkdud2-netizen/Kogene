"""업로드 자원에서 범용 분석 특이도(교차반응) 후보를 생성한다.

등록 패널 밖의 병원체도 같은 속·바이러스군의 근연 자원과 동일 임상
증후군 자원을 찾아 특이도 검토 목록에 포함한다. 생성 결과는 시험 설계
후보이며 실제 교차반응 판정은 서열 분석과 실험으로 확정해야 한다.
"""

from __future__ import annotations

import re

import pandas as pd

from cross_reactivity_data import (
    CROSS_REACTIVITY_ROWS,
    TARGET_ALIASES,
    TARGET_LABELS,
    _contains_term,
    gene_evidence_for_query,
)
from inventory_matching import normalize_name, similarity_score


VIRUS_GROUP_TERMS = {
    "adenovirus": ("adenovirus", "mastadenovirus"),
    "alphavirus": ("chikungunya", "mayaro", "venezuelan equine", "eastern equine"),
    "calicivirus": ("norovirus", "sapovirus", "calicivirus", "vesivirus"),
    "coronavirus": ("coronavirus", "alphacoronavirus", "betacoronavirus", "sars", "mers", "covid", "fipv"),
    "enterovirus": ("enterovirus", "coxsackievirus", "echovirus", "poliovirus", "parechovirus"),
    "flavivirus": ("dengue", "zika", "yellow fever", "west nile", "japanese encephalitis",
                    "tick borne encephalitis", "st louis encephalitis", "flavivirus"),
    "herpesvirus": ("herpes", "herpesvirus", "herpesviridae", "hsv", "varicella", "cytomegalovirus", "epstein barr", "cmv", "ebv"),
    "influenza": ("influenza", "flu a", "flu b"),
    "orthopoxvirus": ("mpox", "monkeypox", "vaccinia", "orthopox"),
    "paramyxovirus": ("parainfluenza", "metapneumovirus", "respiratory syncytial", "rsv",
                      "measles", "mumps", "paramyxovirus"),
    "parvovirus": ("parvovirus", "bocavirus", "panleukopenia"),
    "circovirus": ("circovirus", "pcv 1", "pcv 2"),
    "reovirus": ("rotavirus", "reovirus", "orthoreovirus"),
    "retrovirus": ("hiv", "htlv", "immunodeficiency virus", "lymphotropic virus",
                   "lentivirus", "gammaretrovirus"),
}

SYSTEM_RULES = {
    "장관계": (
        "aeromonas", "astrovirus", "bacillus cereus", "campylobacter", "citrobacter", "clostridioides",
        "clostridium difficile", "clostridium perfringens", "cryptosporidium", "cyclospora",
        "eiec", "epec", "stec", "eaec", "etec", "escherichia coli", "helicobacter",
        "edwardsiella", "hafnia", "listeria", "morganella", "norovirus", "pantoea",
        "plesiomonas", "pseudescherichia", "rotavirus", "salmonella", "sapovirus",
        "shigella", "vibrio", "yersinia",
    ),
    "호흡기계": (
        "adenovirus", "alphacoronavirus", "betacoronavirus", "bocavirus", "bordetella", "chlamydophila pneumoniae", "coronavirus", "influenza",
        "legionella", "metapneumovirus", "moraxella", "morexella", "mycobacterium",
        "mycoplasma pneumoniae", "parainfluenza", "respiratory syncytial", "rhinovirus",
        "sars", "streptococcus pneumoniae",
    ),
    "혈액매개": (
        "babesia", "hepatitis b", "hepatitis c", "hiv", "htlv", "immunodeficiency virus",
        "lymphotropic virus", "plasmodium",
    ),
    "중추신경계": (
        "coxsackie", "echovirus", "encephalitis", "enterovirus", "herpes virus 1",
        "herpes virus 2", "mening", "mumps", "neisseria meningitidis", "parechovirus",
        "poliovirus", "toxoplasma",
    ),
    "발열·매개체": (
        "babesia", "borrelia", "chikungunya", "dengue", "encephalitis", "francisella",
        "hantaan", "lassa", "leptospira", "malaria", "mayaro", "plasmodium",
        "rickettsia", "seoul orthohantavirus", "toxoplasma", "west nile", "yellow fever", "zika",
    ),
    "비뇨생식기계": (
        "candida", "chlamydia trachomatis", "enterococcus", "escherichia coli",
        "haemophilus ducreyi", "mycoplasma genitalium", "neisseria gonorrhoeae",
        "proteus mirabilis", "pseudomonas aeruginosa", "staphylococcus saprophyticus",
        "streptococcus agalactiae", "trichomonas", "ureaplasma",
    ),
    "혈류·상처": (
        "acinetobacter", "bacteroides fragilis", "candida", "citrobacter", "enterobacter", "enterococcus",
        "escherichia coli", "hafnia", "klebsiella", "morganella", "pantoea", "proteus", "pseudomonas", "serratia",
        "staphylococcus aureus", "staphylococcus epidermidis", "streptococcus agalactiae",
    ),
    "피부·점막": (
        "cutibacterium", "pyramidobacter", "staphylococcus", "streptococcus pyogenes",
    ),
    "동물 호흡기·전신": (
        "actinobacillus", "avian", "bovine", "canine", "circovirus", "feline", "gallid",
        "infectious bronchitis", "infectious bursal", "marek", "pasteurella", "pcv 2",
        "porcine", "prrsv", "swine influenza",
    ),
}

NON_PATHOGEN_TERMS = (
    "axis deer", "bison", "bovine male", "chicken male", "clam", "control genomic dna", "crab",
    "donkey", "duck", "fish salmon", "goat", "goose", "guinea pig", "horse male", "lobster",
    "monkey rhesus", "mouse icr", "mussels", "oyster", "pigeon", "porcine male", "quail",
    "sheep", "shrimp", "squid", "turkey",
)

KIND_TERMS = {
    "기생충": ("babesia", "cryptosporidium", "cyclospora", "plasmodium", "toxoplasma", "trichomonas"),
    "진균": ("aspergillus", "candida", "cryptococcus", "fung", "pneumocystis", "yeast"),
}

SCOPE_PRIORITY = {"재고 기반 근연 후보": 4, "재고 기반 증후군 후보": 2}
# 분류 규칙의 선언 순서를 그대로 우선순위로 사용한다. 새 분류를
# SYSTEM_RULES에 추가했는데 이 목록에서 빠뜨려 StopIteration이 발생하는
# 상황을 구조적으로 방지한다.
SYSTEM_PRIORITY = (*SYSTEM_RULES, "기타")
OUTPUT_SCOPE_PRIORITY = {
    "표적 직접 연관": 0,
    "직접 검색": 1,
    "재고 기반 근연 후보": 2,
    "질환군 전체": 3,
    "증후군 확장": 4,
    "재고 기반 증후군 후보": 5,
    "기본 패널": 6,
    "사용자 입력": 7,
}
VALIDATION_PRIORITY_ORDER = {"필수": 0, "권장": 1, "참고": 2}


def _normalized(value: str) -> str:
    return normalize_name(value).replace("-", " ")


def infer_kind(name: str) -> str:
    text = _normalized(name)
    if any(term in text for term in KIND_TERMS["기생충"]):
        return "기생충"
    if any(term in text for term in KIND_TERMS["진균"]):
        return "진균"
    if re.search(r"\bh\d+n\d+\b", text) or any(term in text for terms in VIRUS_GROUP_TERMS.values() for term in terms) or any(
        term in text for term in ("virus", "viridae", "viral", "prrsv", "pcv")
    ):
        return "바이러스"
    return "세균"


def infer_systems(name: str) -> set[str]:
    text = _normalized(name)
    return {
        system for system, terms in SYSTEM_RULES.items()
        if any(_contains_term(text, term) for term in terms)
    }


def _primary_system(systems: set[str]) -> str:
    """여러 분류 중 대표 분류를 고르며 알 수 없는 값에도 안전하게 대응한다."""
    return next((value for value in SYSTEM_PRIORITY if value in systems), "기타")


def related_group(name: str) -> str:
    """세균·진균·기생충은 주로 속, 바이러스는 임상적으로 유용한 군으로 묶는다."""
    text = _normalized(name).replace("mycobaterium", "mycobacterium")
    if re.search(r"\bh\d+n\d+\b", text):
        return "influenza"
    for group, terms in VIRUS_GROUP_TERMS.items():
        if any(_contains_term(text, term) for term in terms):
            return group
    stop = {
        "control", "dna", "from", "genomic", "human", "inactivated", "quantitative",
        "rna", "synthetic", "virus", "viral", "nattrol",
    }
    return next((token for token in text.split() if token not in stop and len(token) >= 4), "")


def _canonical_target(query: str) -> str:
    text = (query or "").strip().lower()
    gene_profiles = gene_evidence_for_query(query)
    if len(gene_profiles) == 1:
        return gene_profiles[0]["canonical"]
    for key, aliases in TARGET_ALIASES.items():
        if any(_contains_term(text, alias) for alias in aliases):
            label = TARGET_LABELS[key]
            if key == "listeria":
                return "Listeria monocytogenes"
            return label
    return query


def _display_name(value: str) -> str:
    text = str(value).strip()
    text = re.sub(r"^(?:RNA|DNA) from\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\s+(?:(?:genomic|quantitative|synthetic|purified)\s+)?"
        r"(?:RNA|DNA)(?:\s+Control)?(?:[,;].*)?$",
        "", text, flags=re.IGNORECASE,
    )
    return text.strip(" ,;")


def _candidate_inventory_rows(inventory: pd.DataFrame):
    seen = set()
    for _, record in inventory.iterrows():
        raw_name = str(record.get("inventory_name", "")).strip()
        normalized = _normalized(raw_name)
        if not normalized or any(term in normalized for term in NON_PATHOGEN_TERMS):
            continue
        display = _display_name(raw_name)
        identity = _normalized(display)
        if not identity or identity in seen:
            continue
        seen.add(identity)
        yield display, identity


def expand_user_pathogen_rows(rows: list[dict], target_queries):
    """일반 균주·병원체명을 분류하고 해당 증후군의 기본 후보로 확장한다.

    등록 타겟/별칭에 없는 학명도 SYSTEM_RULES로 질환군을 추론할 수 있으면
    더 이상 ``기타/미분류`` 입력으로만 남기지 않는다. 균주 식별자(ATCC,
    KCTC 등)가 뒤에 붙어도 종명이 보존되므로 같은 규칙으로 처리된다.
    """
    output = [dict(item) for item in rows]
    output_by_key = {
        (item["system"], item["kind"], item["organism"]): item for item in output
    }
    classified_targets = set()

    for query in target_queries:
        target = (query or "").strip()
        if not target:
            continue
        systems = infer_systems(target)
        if not systems:
            continue

        classified_targets.add(target.casefold())
        primary_system = _primary_system(systems)
        for item in output:
            if (
                item.get("scope") == "사용자 입력"
                and str(item.get("organism", "")).casefold() == target.casefold()
            ):
                item.update({
                    "system": primary_system,
                    "kind": infer_kind(target),
                    "basis": "입력한 균주·병원체명을 기반으로 질환군과 병원체 유형을 자동 분류했습니다.",
                })

        for catalog_item in CROSS_REACTIVITY_ROWS:
            if catalog_item["system"] not in systems:
                continue
            key = (catalog_item["system"], catalog_item["kind"], catalog_item["organism"])
            existing = output_by_key.get(key)
            if existing is not None:
                existing["input_targets"] = tuple(dict.fromkeys((
                    *existing.get("input_targets", ()), target,
                )))
                continue
            copied = dict(catalog_item)
            copied.update({
                "scope": "증후군 확장",
                "relation": "증후군 감별 병원체",
                "basis": f"입력 균주가 속한 {catalog_item['system']} 질환군에서 함께 검토할 확장 후보",
                "input_targets": (target,),
            })
            output.append(copied)
            output_by_key[key] = copied

    return output, classified_targets


def augment_rows_from_inventory(rows: list[dict], target_queries, inventory: pd.DataFrame | None):
    """검색 타겟별 근연군·동일 증후군 후보를 업로드 자원에서 추가한다."""
    if inventory is None or inventory.empty:
        return rows, set()

    output = [dict(item) for item in rows]
    existing = {_normalized(item["organism"]) for item in output}
    output_by_identity = {_normalized(item["organism"]): item for item in output}
    resolved_targets = set()
    candidates = list(_candidate_inventory_rows(inventory))

    for query in target_queries:
        target = (query or "").strip()
        if not target:
            continue
        canonical = _canonical_target(target)
        group = related_group(canonical)
        target_systems = infer_systems(canonical) or infer_systems(target)
        for item in output:
            if target in item.get("input_targets", ()) and item.get("system") != "기타":
                target_systems.add(item["system"])

        added_for_target = 0
        for display, identity in candidates:
            candidate_group = related_group(display)
            candidate_systems = infer_systems(display)
            same_group = bool(group and candidate_group == group)
            shared_systems = target_systems.intersection(candidate_systems)
            if not same_group and not shared_systems:
                continue

            score, _ = similarity_score(canonical, display)
            if score >= 97:
                continue
            if same_group:
                scope = "재고 기반 근연 후보"
                relation = "근연종·형"
                basis = f"검색 병원체와 같은 속 또는 바이러스군({group})에 속하는 사내 자원"
            else:
                scope = "재고 기반 증후군 후보"
                relation = "동일 증후군 감별 병원체"
                basis = "검색 병원체와 임상 증후군·검체 범주가 겹치는 사내 자원"
            possible_systems = shared_systems or target_systems or candidate_systems or {"기타"}
            system = _primary_system(possible_systems)
            if identity in existing:
                existing_item = output_by_identity[identity]
                if existing_item.get("scope") in SCOPE_PRIORITY:
                    related_targets = tuple(dict.fromkeys((*existing_item.get("input_targets", ()), target)))
                    if SCOPE_PRIORITY[scope] > SCOPE_PRIORITY[existing_item["scope"]]:
                        existing_item.update({
                            "system": system, "kind": infer_kind(display), "relation": relation,
                            "basis": basis, "scope": scope,
                        })
                    existing_item["input_targets"] = related_targets
                    added_for_target += 1
                continue
            output.append({
                "system": system,
                "kind": infer_kind(display),
                "organism": display,
                "relation": relation,
                "basis": basis,
                "targets": (),
                "aliases": (),
                "scope": scope,
                "input_targets": (target,),
            })
            existing.add(identity)
            output_by_identity[identity] = output[-1]
            added_for_target += 1

        if added_for_target:
            resolved_targets.add(target.casefold())

    # 실제 후보가 생성된 입력은 단순 사용자 입력 placeholder를 제거한다.
    if resolved_targets:
        output = [
            item for item in output
            if not (
                item.get("scope") == "사용자 입력"
                and str(item.get("organism", "")).casefold() in resolved_targets
            )
        ]
    output.sort(key=lambda item: OUTPUT_SCOPE_PRIORITY.get(item.get("scope", ""), 99))
    return output, resolved_targets


def assign_specificity_metadata(rows: list[dict]) -> list[dict]:
    """특이도 후보를 근연성·임상 관련성에 따라 필수/권장/참고로 분류한다."""
    output = []
    for item in rows:
        copied = dict(item)
        scope = copied.get("scope", "")
        relation = copied.get("relation", "")
        if "근연" in relation or scope == "재고 기반 근연 후보":
            priority = "필수"
        elif scope == "재고 기반 증후군 후보" or (
            scope in {"표적 직접 연관", "직접 검색", "질환군 전체"}
            and any(term in relation for term in ("감별", "동시감염"))
        ):
            priority = "권장"
        else:
            priority = "참고"
        copied["검증 구분"] = "특이도"
        copied["우선순위"] = priority
        output.append(copied)
    output.sort(key=lambda item: (
        VALIDATION_PRIORITY_ORDER.get(item["우선순위"], 99),
        OUTPUT_SCOPE_PRIORITY.get(item.get("scope", ""), 99),
        item.get("organism", "").casefold(),
    ))
    return output


def build_inclusivity_rows(target_queries, inventory: pd.DataFrame | None) -> list[dict]:
    """타겟 자체와 동일 종·strain·혈청형 자원을 포괄성 후보로 구성한다."""
    candidates = list(_candidate_inventory_rows(inventory)) if inventory is not None and not inventory.empty else []
    output = []
    seen_pairs = set()
    for query in target_queries:
        target = (query or "").strip()
        if not target:
            continue
        gene_profiles = gene_evidence_for_query(target)
        canonical = _canonical_target(target)
        canonical_is_more_specific = (
            _normalized(canonical) != _normalized(target)
            and len(_normalized(canonical).split()) >= 2
        )
        matched = []
        for display, identity in candidates:
            profile_match = any(
                any(_contains_term(_normalized(display), taxon) for taxon in profile["positive_taxa"])
                for profile in gene_profiles
            )
            canonical_score, _ = similarity_score(canonical, display)
            query_score, _ = similarity_score(target, display)
            score = 100.0 if profile_match else (
                canonical_score if canonical_is_more_specific else max(canonical_score, query_score)
            )
            if score >= 97:
                matched.append((display, identity, score))

        # 유전자 입력은 업로드 재고에 없는 대표 종도 양성 포괄성 범위에
        # 포함한다. 예: invA의 S. enterica/S. bongori, iap의 Listeria spp.
        for catalog_item in CROSS_REACTIVITY_ROWS:
            display = catalog_item["organism"]
            identity = _normalized(display)
            if any(
                any(_contains_term(identity, taxon) for taxon in profile["positive_taxa"])
                for profile in gene_profiles
            ) and identity not in {item[1] for item in matched}:
                matched.append((display, identity, 100.0))

        # 보유 자원이 없어도 타겟 자체는 포괄성 시험 항목으로 유지한다.
        if not matched:
            display = canonical or target
            matched = [(display, _normalized(display), 0.0)]

        for display, identity, score in matched:
            pair = (identity, target.casefold())
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            if score == 100:
                relation = "타겟 일치 자원"
                basis = "검색 타겟과 정규화 명칭이 일치하는 포괄성 확인 자원"
                priority = "필수"
            elif score >= 97:
                relation = "동일 종·strain·형"
                basis = "검색 타겟과 동일 종 또는 지정 유전형 범위의 포괄성 확인 자원"
                priority = "필수"
            else:
                relation = "타겟 기준 항목"
                basis = "보유 자원이 없어도 포괄성 시험 설계에서 확인해야 하는 검색 타겟"
                priority = "권장"
            systems = infer_systems(canonical) or infer_systems(display) or {"기타"}
            system = _primary_system(systems)
            output.append({
                "system": system,
                "kind": infer_kind(display),
                "organism": display,
                "relation": relation,
                "basis": basis,
                "targets": (),
                "aliases": (),
                "scope": "포괄성 직접 후보",
                "input_targets": (target,),
                "검증 구분": "포괄성",
                "우선순위": priority,
            })
    output.sort(key=lambda item: (
        VALIDATION_PRIORITY_ORDER.get(item["우선순위"], 99),
        item["organism"].casefold(),
    ))
    return output


def exclude_inclusivity_from_specificity(specificity_rows: list[dict], inclusivity_rows: list[dict]) -> list[dict]:
    """같은 타겟의 포괄성 항목이 특이도 배제 후보로 중복되는 것을 막는다."""
    inclusivity_pairs = {
        (_normalized(item["organism"]), str(target).casefold())
        for item in inclusivity_rows
        for target in item.get("input_targets", ())
    }
    output = []
    for item in specificity_rows:
        identity = _normalized(item["organism"])
        related_targets = tuple(
            target for target in item.get("input_targets", ())
            if (identity, str(target).casefold()) not in inclusivity_pairs
        )
        if item.get("input_targets") and not related_targets:
            continue
        copied = dict(item)
        if related_targets:
            copied["input_targets"] = related_targets
        output.append(copied)
    return output
