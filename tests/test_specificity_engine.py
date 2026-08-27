import pandas as pd

from cross_reactivity_data import select_cross_reactivity_rows_for_targets
from specificity_engine import (
    assign_specificity_metadata,
    augment_rows_from_inventory,
    build_inclusivity_rows,
    exclude_inclusivity_from_specificity,
    infer_kind,
    infer_systems,
    related_group,
)


def _inventory(*names):
    return pd.DataFrame({"inventory_name": names})


def _expanded(query, inventory):
    rows, _, unrecognized = select_cross_reactivity_rows_for_targets([query])
    rows, resolved = augment_rows_from_inventory(rows, [query], inventory)
    return rows, unrecognized, resolved


def test_unregistered_bacterium_gets_related_and_same_syndrome_candidates():
    rows, unrecognized, resolved = _expanded(
        "Francisella tularensis",
        _inventory(
            "Francisella tularensis DNA Control",
            "Francisella novicida genomic DNA",
            "Dengue virus type 3 RNA Control",
            "Staphylococcus epidermidis DNA",
        ),
    )

    assert unrecognized == ["Francisella tularensis"]
    assert resolved == {"francisella tularensis"}
    assert not any(item["scope"] == "사용자 입력" for item in rows)
    related = next(item for item in rows if item["organism"] == "Francisella novicida")
    assert related["scope"] == "재고 기반 근연 후보"
    assert related["system"] == "발열·매개체"
    assert any(item["organism"] == "Dengue virus type 3" for item in rows)
    assert not any(item["organism"].startswith("Francisella tularensis") for item in rows)


def test_virus_family_and_syndrome_are_both_used():
    rows, _, resolved = _expanded(
        "Mayaro virus",
        _inventory(
            "Mayaro virus RNA Control",
            "Chikungunya virus RNA Control",
            "Dengue virus type 4 RNA Control",
            "Candida albicans DNA",
        ),
    )

    assert resolved == {"mayaro virus"}
    chikungunya = next(item for item in rows if item["organism"] == "Chikungunya virus")
    dengue = next(item for item in rows if item["organism"] == "Dengue virus type 4")
    assert chikungunya["scope"] == "재고 기반 근연 후보"
    assert dengue["scope"] == "재고 기반 증후군 후보"
    assert rows.index(chikungunya) < rows.index(dengue)


def test_known_listeria_panel_is_extended_with_inventory_relatives_without_target_itself():
    rows, unrecognized, resolved = _expanded(
        "Listeria",
        _inventory(
            "Listeria monocytogenes DNA Control",
            "Listeria grayi genomic DNA",
            "Salmonella Typhi DNA",
        ),
    )

    assert not unrecognized
    assert resolved == {"listeria"}
    assert any(item["organism"] == "Listeria grayi" for item in rows)
    assert not any(item["organism"].startswith("Listeria monocytogenes") for item in rows)
    assert all(item["input_targets"] == ("Listeria",) for item in rows)


def test_truly_unrelated_custom_text_remains_for_manual_review():
    rows, _, resolved = _expanded(
        "Unknown custom target",
        _inventory("Listeria monocytogenes", "Influenza A virus"),
    )
    assert not resolved
    assert len(rows) == 1
    assert rows[0]["scope"] == "사용자 입력"


def test_multiplex_inventory_candidates_merge_related_target_labels():
    queries = ["Mayaro virus", "Yellow fever virus"]
    rows, _, _ = select_cross_reactivity_rows_for_targets(queries)
    rows, resolved = augment_rows_from_inventory(
        rows,
        queries,
        _inventory(
            "Mayaro virus RNA Control",
            "Yellow fever virus RNA Control",
            "Dengue virus type 3 RNA Control",
        ),
    )
    dengue = next(item for item in rows if item["organism"] == "Dengue virus type 3")
    assert resolved == {"mayaro virus", "yellow fever virus"}
    assert dengue["input_targets"] == ("Mayaro virus", "Yellow fever virus")


def test_kind_system_and_related_group_classification():
    assert infer_kind("Dengue virus type 3") == "바이러스"
    assert infer_kind("Candida albicans") == "진균"
    assert infer_kind("Plasmodium vivax") == "기생충"
    assert infer_kind("Francisella tularensis") == "세균"
    assert {"중추신경계", "발열·매개체"}.issubset(infer_systems("Japanese encephalitis virus"))
    assert related_group("Dengue virus type 3") == "flavivirus"
    assert related_group("Mycobacterium tuberculosis") == "mycobacterium"


def test_inclusivity_contains_target_strains_but_not_other_species():
    inventory = _inventory(
        "Listeria monocytogenes DNA Control",
        "Listeria monocytogenes strain EGD-e genomic DNA",
        "Listeria innocua genomic DNA",
    )
    rows = build_inclusivity_rows(["Listeria"], inventory)
    assert {item["organism"] for item in rows} == {
        "Listeria monocytogenes", "Listeria monocytogenes strain EGD-e",
    }
    assert all(item["검증 구분"] == "포괄성" and item["우선순위"] == "필수" for item in rows)


def test_inclusivity_items_are_removed_only_from_same_target_specificity_rows():
    inclusivity = [{
        "organism": "Dengue virus type 3", "input_targets": ("Dengue 3",),
    }]
    specificity = [{
        "organism": "Dengue virus type 3",
        "input_targets": ("Dengue 3", "Zika virus"),
        "scope": "재고 기반 근연 후보",
    }]
    filtered = exclude_inclusivity_from_specificity(specificity, inclusivity)
    assert filtered[0]["input_targets"] == ("Zika virus",)


def test_specificity_priorities_separate_required_recommended_and_reference():
    rows = assign_specificity_metadata([
        {"organism": "A", "relation": "근연종", "scope": "표적 직접 연관"},
        {"organism": "B", "relation": "동일 증후군 감별 병원체", "scope": "재고 기반 증후군 후보"},
        {"organism": "C", "relation": "증후군 감별 병원체", "scope": "증후군 확장"},
    ])
    assert [(item["organism"], item["우선순위"]) for item in rows] == [
        ("A", "필수"), ("B", "권장"), ("C", "참고"),
    ]
    assert all(item["검증 구분"] == "특이도" for item in rows)
