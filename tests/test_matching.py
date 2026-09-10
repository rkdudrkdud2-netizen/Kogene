import pytest

from cross_reactivity_data import select_cross_reactivity_rows, select_cross_reactivity_rows_for_targets
from inventory_matching import excel_safe_value, find_all_matches, find_best_match, read_inventory, similarity_score


class Upload:
    name = "inventory.csv"
    def __init__(self, data): self.data = data
    def getvalue(self): return self.data


def test_abbreviation_and_control_suffix_match():
    score, _ = similarity_score("Escherichia coli", "E. coli genomic DNA control")
    assert score == 100


def test_inventory_header_detection_and_matching():
    data = "설명,사내 자원 목록\n관리번호,표준물질 균주명\nZ001,E. coli genomic DNA\n".encode("utf-8-sig")
    result = find_best_match("Escherichia coli", (), read_inventory(Upload(data)), threshold=86)
    assert result.owned
    assert result.inventory_id == "Z001"


def test_blank_management_number_header_is_inferred():
    data = "설명,사내 자원 목록\n,표준물질 균주명\nZ001,E. coli genomic DNA\nZ002,Salmonella enterica\n".encode("utf-8-sig")
    result = find_best_match("Salmonella enterica", (), read_inventory(Upload(data)), threshold=86)
    assert result.owned
    assert result.inventory_id == "Z002"


def test_all_management_numbers_are_retained():
    data = "관리번호,표준물질 균주명\nZ101,Salmonella enterica\nZ102,Salmonella enterica strain A\n".encode("utf-8-sig")
    matches = find_all_matches("Salmonella enterica", (), read_inventory(Upload(data)), threshold=86)
    assert [match.inventory_id for match in matches] == ["Z101", "Z102"]


def test_target_selection_and_disease_name_rejection():
    rows, interpretation = select_cross_reactivity_rows("stx1/stx2")
    assert "STEC" in interpretation
    assert any(item["organism"] == "Escherichia albertii" for item in rows)
    respiratory, interpretation = select_cross_reactivity_rows("호흡기계 감염증")
    assert respiratory == []
    assert "질환명은 검색 대상이 아닙니다" in interpretation


def test_ehec_returns_comprehensive_gastrointestinal_panel():
    rows, interpretation = select_cross_reactivity_rows("EHEC")
    bacteria = [item for item in rows if item["kind"] == "세균"]
    viruses = [item for item in rows if item["kind"] == "바이러스"]
    assert "세균+바이러스" in interpretation
    assert len(rows) == 27
    assert len(bacteria) == 19
    assert len(viruses) == 8
    assert all(item["system"] == "장관계" for item in rows)
    assert {item["scope"] for item in rows} == {"표적 직접 연관", "증후군 확장"}
    assert sum(item["scope"] == "표적 직접 연관" for item in rows) == 9


def test_respiratory_target_expands_only_within_respiratory_system():
    rows, interpretation = select_cross_reactivity_rows("SARS-CoV-2 N")
    assert "세균+바이러스" in interpretation
    assert len(rows) == 21
    assert {item["kind"] for item in rows} == {"세균", "바이러스"}
    assert all(item["system"] == "호흡기계" for item in rows)


@pytest.mark.parametrize(("query", "system", "expected_total", "bacteria", "viruses"), [
    ("EHEC", "장관계", 27, 19, 8),
    ("ipaH", "장관계", 27, 19, 8),
    ("invA", "장관계", 27, 19, 8),
    ("C. jejuni", "장관계", 27, 19, 8),
    ("C. difficile", "장관계", 27, 19, 8),
    ("Norovirus", "장관계", 27, 19, 8),
    ("Rotavirus", "장관계", 27, 19, 8),
    ("Listeria monocytogenes", "장관계", 27, 19, 8),
    ("SARS-CoV-2", "호흡기계", 21, 9, 12),
    ("Influenza", "호흡기계", 21, 9, 12),
    ("RSV", "호흡기계", 21, 9, 12),
    ("B. pertussis", "호흡기계", 21, 9, 12),
    ("M. pneumoniae", "호흡기계", 21, 9, 12),
])
def test_every_supported_target_gets_its_full_syndrome_panel(
    query, system, expected_total, bacteria, viruses,
):
    rows, interpretation = select_cross_reactivity_rows(query)
    assert "포괄 패널" in interpretation
    assert len(rows) == expected_total
    assert sum(item["kind"] == "세균" for item in rows) == bacteria
    assert sum(item["kind"] == "바이러스" for item in rows) == viruses
    assert all(item["system"] == system for item in rows)
    assert {item["scope"] for item in rows} == {"표적 직접 연관", "증후군 확장"}


@pytest.mark.parametrize("query", [
    "Listeria", "Listeria monocytogenes", "L. monocytogenes", "리스테리아", "hlyA", "prfA",
])
def test_listeria_names_and_target_genes_are_recognized(query):
    rows, interpretation, unrecognized = select_cross_reactivity_rows_for_targets([query])
    assert not unrecognized
    assert "Listeria monocytogenes" in interpretation
    assert any(item["organism"] == "Listeria innocua" for item in rows)
    assert all(item["system"] == "장관계" for item in rows)


def test_targets_from_both_systems_return_combined_full_panel():
    rows, interpretation = select_cross_reactivity_rows("EHEC + SARS-CoV-2 N")
    assert "장관계/호흡기계" in interpretation
    assert len(rows) == 48
    assert {item["system"] for item in rows} == {"장관계", "호흡기계"}


def test_multiplex_targets_keep_only_their_related_input_labels():
    rows, interpretation, unrecognized = select_cross_reactivity_rows_for_targets(["Plasmodium", "Salmonella"])
    assert not unrecognized
    assert "Plasmodium" in interpretation and "Salmonella" in interpretation
    assert "혈액매개 기생충" in interpretation
    assert len(rows) == 34
    malaria_row = next(item for item in rows if item["organism"] == "Plasmodium falciparum")
    salmonella_row = next(item for item in rows if item["organism"] == "Salmonella bongori")
    assert malaria_row["input_targets"] == ("Plasmodium",)
    assert salmonella_row["input_targets"] == ("Salmonella",)


def test_same_syndrome_multiplex_rows_merge_both_target_labels():
    rows, _, unrecognized = select_cross_reactivity_rows_for_targets(["EHEC", "Salmonella"])
    assert not unrecognized
    assert len(rows) == 27
    assert all(item["input_targets"] == ("EHEC", "Salmonella") for item in rows)


def test_unregistered_target_is_kept_for_inventory_matching_and_reported_for_review():
    rows, _, unrecognized = select_cross_reactivity_rows_for_targets(["Unknown custom target", "Salmonella"])
    assert unrecognized == ["Unknown custom target"]
    custom = next(item for item in rows if item["organism"] == "Unknown custom target")
    assert custom["scope"] == "사용자 입력"
    assert custom["system"] == "기타"
    assert custom["input_targets"] == ("Unknown custom target",)
    assert any(item["input_targets"] == ("Salmonella",) for item in rows)


@pytest.mark.parametrize("query", [
    "Shigella sonnei", "Yersinia enterocolitica", "Bordetella holmesii",
    "Human metapneumovirus", "Babesia divergens",
])
def test_every_catalog_pathogen_can_be_used_as_a_search_target(query):
    rows, interpretation, unrecognized = select_cross_reactivity_rows_for_targets([query])
    assert not unrecognized
    assert "포괄 패널" in interpretation
    assert any(item["scope"] in {"표적 직접 연관", "직접 검색"} for item in rows)
    assert all(item["input_targets"] == (query,) for item in rows)


@pytest.mark.parametrize(("target", "different_organism"), [
    ("Influenza A virus", "Influenza B virus"),
    ("Norovirus GI", "Norovirus GII"),
    ("Respiratory syncytial virus A", "Respiratory syncytial virus B"),
    ("Human coronavirus OC43", "Human coronavirus 229E"),
    ("Bordetella pertussis", "Bordetella parapertussis"),
])
def test_distinct_species_and_subtypes_do_not_cross_match(target, different_organism):
    score, method = similarity_score(target, different_organism)
    assert score < 70
    assert method == "종·아형 불일치"


def test_alias_cannot_override_primary_subtype_conflict_at_low_threshold():
    score, method = similarity_score("Norovirus GI", "Norovirus GII", ("Norwalk virus GI",))
    assert score < 70
    assert method == "종·아형 불일치"


def test_valid_virus_alias_still_matches():
    score, _ = similarity_score("SARS-CoV-1", "SARS coronavirus isolate", ("SARS coronavirus",))
    assert score >= 86


@pytest.mark.parametrize(("target", "different_organism"), [
    ("Streptococcus pneumoniae", "Klebsiella pneumoniae"),
    ("Streptococcus pneumoniae", "Mycoplasma pneumoniae"),
    ("Human parainfluenza virus 1", "HIV-1 RNA"),
    ("Influenza B virus", "Swine influenza virus"),
    ("Rotavirus B", "Rotavirus"),
    ("SARS-CoV-1", "SARS-CoV-2 BA.1.1"),
])
def test_shared_words_do_not_create_false_inventory_matches(target, different_organism):
    score, _ = similarity_score(target, different_organism)
    assert score < 70


def test_minor_genus_typo_remains_matchable():
    score, _ = similarity_score("Moraxella catarrhalis", "Morexella catarrhalis")
    assert score >= 86


@pytest.mark.parametrize("inventory_name", ["Adenovirus type 40", "Human adenovirus 41"])
def test_combined_adenovirus_types_match_either_requested_type(inventory_name):
    score, _ = similarity_score(
        "Human adenovirus F40/41",
        inventory_name,
        ("Enteric adenovirus 40", "Enteric adenovirus 41"),
    )
    assert score >= 86


def test_short_target_alias_does_not_match_inside_another_word():
    rows, interpretation = select_cross_reactivity_rows("HPIV1 respiratory panel")
    assert "M. pneumoniae" not in interpretation
    assert len(rows) == 1 and rows[0]["scope"] == "사용자 입력"


def test_url_rows_are_not_accepted_as_organism_inventory():
    data = "제품명,관리번호\nhttps://example.com/catalog,Z001\n".encode("utf-8-sig")
    with pytest.raises(ValueError, match="미생물명 열"):
        read_inventory(Upload(data))


def test_short_id_hint_does_not_match_validity_column():
    data = "validity,표준물질 균주명\n2027-01-01,Escherichia coli\n".encode("utf-8-sig")
    inventory = read_inventory(Upload(data))
    assert inventory.iloc[0]["inventory_id"] == ""


@pytest.mark.parametrize("formula", ["=HYPERLINK(\"https://example.com\")", "+1+1", "-2+3", "@SUM(A1:A2)"])
def test_download_text_cannot_become_excel_formula(formula):
    assert excel_safe_value(formula).startswith("'")
