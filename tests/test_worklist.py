from inventory_matching import MatchResult, read_inventory
from worklist import build_worklist_rows, parse_quantity, resource_readiness


class Upload:
    name = "inventory.csv"

    def __init__(self, data):
        self.data = data

    def getvalue(self):
        return self.data


def _match(**values):
    defaults = {
        "owned": True, "score": 100.0, "method": "정규화 일치",
        "inventory_name": "Escherichia coli", "inventory_id": "Z001",
        "catalog_no": "00123", "sheet": "Sheet1", "purchase_date": "2024-01-01",
        "initial_volume_ul": "50", "cumulative_use_ul": "34",
        "remaining_volume_ul": "16", "dilution_tubes": "9", "notes": "",
    }
    defaults.update(values)
    return MatchResult(**defaults)


def test_quantity_parser_normalizes_ul_tubes_and_exhausted_text():
    assert parse_quantity("500 µL") == 500
    assert parse_quantity("9개") == 9
    assert parse_quantity("소진") == 0
    assert parse_quantity(2.5) == 2.5
    assert parse_quantity("") is None


def test_resource_readiness_and_inventory_balance_check():
    assert resource_readiness(_match()) == ("즉시 사용 가능", "정상")
    status, check = resource_readiness(_match(
        cumulative_use_ul="47", remaining_volume_ul="소진", dilution_tubes="9",
    ))
    assert status == "즉시 사용 가능"
    assert "계산 잔량 3 µL" in check
    assert resource_readiness(_match(
        cumulative_use_ul="50", remaining_volume_ul="소진", dilution_tubes="소진",
    )) == ("소진", "정상")


def test_all_matching_resources_are_expanded_without_priority_selection():
    first = _match(inventory_id="Z001")
    second = _match(inventory_id="Z002", dilution_tubes="소진")
    results = [{
        "organism": "Escherichia coli", "relation": "근연종", "scope": "표적 직접 연관",
        "system": "장관계", "kind": "세균",
        "매칭 점수": 100.0, "자원 상세": [first, second],
    }]
    rows = build_worklist_rows(results, "Multiplex qPCR", "stx1 + stx2")
    assert [row["관리번호"] for row in rows] == ["Z001", "Z002"]
    assert all(row["qPCR 구성"] == "Multiplex qPCR" for row in rows)
    assert all(row["질환군"] == "장관계" and row["병원체 유형"] == "세균" for row in rows)


def test_worklist_preserves_every_dynamic_system_and_pathogen_kind():
    results = [
        {
            "organism": "Cutibacterium acnes", "relation": "직접 검색", "scope": "사용자 입력",
            "system": "피부·점막", "kind": "세균", "매칭 점수": 0.0, "자원 상세": [],
        },
        {
            "organism": "Porcine circovirus 2", "relation": "직접 검색", "scope": "사용자 입력",
            "system": "동물 호흡기·전신", "kind": "바이러스", "매칭 점수": 0.0, "자원 상세": [],
        },
    ]

    rows = build_worklist_rows(results, "Multiplex qPCR", "custom targets")

    assert [(row["질환군"], row["병원체 유형"]) for row in rows] == [
        ("피부·점막", "세균"), ("동물 호흡기·전신", "바이러스"),
    ]


def test_inventory_reader_retains_worklist_resource_fields():
    data = (
        "관리번호,시료명/균주명,Cat no.,구매일,최초 원액 용량 (µL),"
        "원액 누적 사용량 (µL),원액 잔량 (µL),희석액(1/100) 튜브 수 (n),비고\n"
        "Z001,Escherichia coli,00123,2024-01-01,50,34,16,9,사용 가능\n"
    ).encode("utf-8-sig")
    inventory = read_inventory(Upload(data))
    record = inventory.iloc[0]
    assert record["purchase_date"] == "2024-01-01"
    assert record["initial_volume_ul"] == "50"
    assert record["cumulative_use_ul"] == "34"
    assert record["remaining_volume_ul"] == "16"
    assert record["dilution_tubes"] == "9"
    assert record["notes"] == "사용 가능"


def test_legacy_match_result_without_new_inventory_fields_does_not_crash():
    class LegacyMatch:
        owned = True
        score = 100.0
        method = "정규화 일치"
        inventory_name = "Escherichia coli"
        inventory_id = "Z001"
        catalog_no = "00123"
        sheet = "Sheet1"

    results = [{
        "organism": "Escherichia coli", "relation": "근연종", "scope": "표적 직접 연관",
        "매칭 점수": 100.0, "자원 상세": [LegacyMatch()],
    }]
    rows = build_worklist_rows(results, "Multiplex qPCR", "stx1 + stx2")
    assert rows[0]["관리번호"] == "Z001"
    assert rows[0]["최초 원액 용량 (µL)"] is None
    assert rows[0]["준비 상태"] == "정보 확인 필요"
    assert rows[0]["재고 점검"] == "정상"
