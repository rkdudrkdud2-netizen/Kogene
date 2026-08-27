from candidate_grouping import group_candidate_rows, representative_organism_name


def test_representative_name_groups_strains_subspecies_serotypes_and_virus_types():
    assert representative_organism_name("Listeria monocytogenes strain EGD-e") == "Listeria monocytogenes"
    assert representative_organism_name("Campylobacter jejuni subsp. jejuni") == "Campylobacter jejuni"
    assert representative_organism_name("Escherichia coli O157:H7") == "Escherichia coli"
    assert representative_organism_name("Dengue virus type 4") == "Dengue virus"
    assert representative_organism_name("Rotavirus A") == "Rotavirus"


def test_grouped_rows_keep_distinct_species_and_aggregate_auditable_details():
    rows = [
        {"organism": "Escherichia coli", "우선순위": "권장", "relation": "근연종", "보유 여부": "보유", "보유 자원 수": 1, "관리번호": "Z1", "input_targets": ("EHEC",)},
        {"organism": "Escherichia coli O157:H7", "우선순위": "필수", "relation": "혈청형", "보유 여부": "보유", "보유 자원 수": 2, "관리번호": "Z1, Z2", "input_targets": ("EHEC",)},
        {"organism": "Escherichia albertii", "우선순위": "권장", "relation": "근연종", "보유 여부": "미보유", "보유 자원 수": 0, "관리번호": "—", "input_targets": ("EHEC",)},
    ]

    grouped = group_candidate_rows(rows)

    assert len(grouped) == 2
    e_coli = grouped[0]
    assert e_coli["대표 병원체"] == "Escherichia coli"
    assert e_coli["세부 후보 수"] == 2
    assert e_coli["우선순위"] == "필수"
    assert e_coli["보유 자원 수"] == 2
    assert e_coli["관리번호"] == "Z1, Z2"
