from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_crosscheck_page_renders_without_exception():
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    assert not app.exception
    assert app.radio[0].value == "교차검증 패널"
    assert [metric.label for metric in app.metric[:4]] == [
        "업로드 자원", "보유 후보종", "매칭 자원", "미보유 후보종",
    ]
    assert [metric.label for metric in app.metric[4:8]] == [
        "즉시 사용 가능", "원액·희석 준비", "소진·미보유", "정보·재고 확인",
    ]
    summary_html = "\n".join(item.value for item in app.markdown)
    assert "포괄성 후보" in summary_html and "특이도 후보" in summary_html
    assert len(app.dataframe) >= 3
    assert {"질환군", "병원체 유형"}.issubset(app.dataframe[0].value.columns)
    assert len(app.download_button) == 1


def test_representative_pathogen_view_is_default_and_can_expand_to_detail_rows():
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()

    assert not app.exception
    assert [control.value for control in app.segmented_control] == [
        "대표 병원체 묶음", "대표 병원체 묶음",
    ]
    assert "대표 병원체" in app.dataframe[1].value.columns
    assert any("세부 후보 8개" in item.value for item in app.caption)

    app.segmented_control[1].set_value("세부 후보 전체").run()

    assert not app.exception
    assert "미생물" in app.dataframe[3].value.columns
    assert "대표 병원체" not in app.dataframe[3].value.columns


def test_distribution_page_navigation_renders_without_exception():
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    app.radio[0].set_value("분양처 안내").run()
    assert not app.exception
    assert [metric.label for metric in app.metric] == ["등록 분양처", "현재 검색 결과", "기관 분류"]
    assert app.metric[0].value == "15곳"
    assert any("American Type Culture Collection" in item.value for item in app.markdown)


def test_single_qpcr_mode_uses_the_same_worklist_flow():
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    app.selectbox[0].set_value("Single qPCR")
    app.run()
    app.text_input[0].set_value("EHEC").run()
    assert not app.exception
    assert app.selectbox[0].value == "Single qPCR"
    assert any(item.value == "Single qPCR 시험 작업 목록" for item in app.subheader)
    summary_html = "\n".join(item.value for item in app.markdown)
    assert "포괄성 후보" in summary_html and "1종" in summary_html
    assert "특이도 후보" in summary_html and "27종" in summary_html


def test_listeria_search_renders_results_without_unrecognized_warning():
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    app.text_input[0].set_value("Listeria").run()

    assert not app.exception
    summary_html = "\n".join(item.value for item in app.markdown)
    assert "포괄성 후보" in summary_html and "1종" in summary_html
    assert "특이도 후보" in summary_html and "27종" in summary_html
    assert not any("지원 패널로 인식하지 못한 타겟" in item.value for item in app.warning)
    assert any("Listeria monocytogenes" in item.value for item in app.caption)


def test_full_strain_name_is_searchable_without_inventory():
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    app.text_input[0].set_value("Escherichia coli ATCC 25922").run()

    assert not app.exception
    assert not any("자동 분류가 필요한" in item.value for item in app.info)
    assert any("균주·병원체명 기반 자동 분류" in item.value for item in app.caption)
    worklist = app.dataframe[0].value
    target_rows = worklist.loc[worklist["추천 미생물"].eq("Escherichia coli ATCC 25922")]
    assert not target_rows.empty
    assert set(target_rows["질환군"]) == {"장관계"}
    assert set(target_rows["병원체 유형"]) == {"세균"}


def test_unregistered_pathogen_still_reaches_results_and_inventory_flow():
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    app.text_input[0].set_value("Emerging pathogen X").run()

    assert not app.exception
    summary_html = "\n".join(item.value for item in app.markdown)
    assert "포괄성 후보" in summary_html and "1종" in summary_html
    assert any("검색과 사내 자원 대조에는 포함했습니다" in item.value for item in app.info)
    worklist = app.dataframe[0].value
    assert worklist.iloc[0]["추천 미생물"] == "Emerging pathogen X"


def test_uploaded_inventory_builds_specificity_panel_for_unregistered_pathogen():
    inventory_csv = (
        "관리번호,표준물질 균주명\n"
        "V001,Mayaro virus RNA Control\n"
        "V002,Chikungunya virus RNA Control\n"
        "V003,Dengue virus type 4 RNA Control\n"
    ).encode("utf-8-sig")
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    app.text_input[0].set_value("Mayaro virus")
    app.file_uploader[0].upload("inventory.csv", inventory_csv, "text/csv")
    app.run()

    assert not app.exception
    assert app.metric[0].value == "3건"
    summary_html = "\n".join(item.value for item in app.markdown)
    assert "포괄성 후보" in summary_html and "1종" in summary_html
    assert "특이도 후보" in summary_html and "2종" in summary_html
    assert not any("자동 분류가 필요한" in item.value for item in app.info)
    worklist = app.dataframe[0].value
    assert set(worklist.loc[worklist["검증 구분"].eq("포괄성"), "추천 미생물"]) == {"Mayaro virus"}
    assert set(worklist.loc[worklist["검증 구분"].eq("특이도"), "추천 미생물"]) == {
        "Chikungunya virus", "Dengue virus type 4",
    }


def test_inventory_upload_runs_through_worklist_without_attribute_error():
    inventory_csv = (
        "관리번호,시료명/균주명,Cat no.,구매일,최초 원액 용량 (µL),"
        "원액 누적 사용량 (µL),원액 잔량 (µL),희석액(1/100) 튜브 수 (n),비고\n"
        "Z001,Salmonella enterica,00123,2024-01-01,50,34,16,9,사용 가능\n"
    ).encode("utf-8-sig")
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    app.text_input[0].set_value("EHEC")
    app.file_uploader[0].upload("inventory.csv", inventory_csv, "text/csv")
    app.run()

    assert not app.exception
    assert app.metric[0].value == "1건"
    assert app.metric[4].value == "1건"
    assert len(app.success) == 1
    assert "자원 레코드 1건" in app.success[0].value


def test_multiplex_target_count_creates_inputs_and_tracks_each_target():
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    app.number_input[0].set_value(3).run()
    assert len(app.text_input) == 3
    app.text_input[0].set_value("Malaria")
    app.text_input[1].set_value("Salmonella")
    app.text_input[2].set_value("")
    app.run()

    assert not app.exception
    worklist = app.dataframe[0].value
    malaria_targets = set(worklist.loc[
        worklist["추천 미생물"].eq("Plasmodium falciparum"), "입력 표적"
    ])
    salmonella_targets = set(worklist.loc[
        worklist["추천 미생물"].eq("Salmonella bongori"), "입력 표적"
    ])
    assert malaria_targets == {"Malaria"}
    assert salmonella_targets == {"Salmonella"}
