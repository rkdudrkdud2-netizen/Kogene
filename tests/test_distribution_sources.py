from distribution_sources import CATEGORIES, DISTRIBUTION_SOURCES, filter_distribution_sources


def test_distribution_source_directory_is_complete_and_unique():
    assert len(DISTRIBUTION_SOURCES) == 15
    assert len({source["name"] for source in DISTRIBUTION_SOURCES}) == 15
    assert len({source["url"] for source in DISTRIBUTION_SOURCES}) == 15
    assert all(source["url"].startswith(("http://", "https://")) for source in DISTRIBUTION_SOURCES)
    assert set(CATEGORIES) == {"국내 공공·연구은행", "해외 공공은행", "해외·상업 분양처"}


def test_verified_distribution_links_use_current_detail_pages():
    sources = {source["acronym"]: source for source in DISTRIBUTION_SOURCES}
    assert sources["KBPV"]["url"].endswith("menu_id=030300")
    assert sources["TB Specimen Bank"]["url"].endswith("menu_cd=04_03_02")
    assert sources["NCCP"]["url"].endswith("menu_id=010100")
    assert sources["MFDS · NIFDS"]["url"].startswith("https://nifds.go.kr/")
    assert "determine-your-distributor" in sources["ATCC"]["contact_url"]


def test_distribution_source_search_finds_tuberculosis_resources():
    results = filter_distribution_sources("결핵")
    assert {source["acronym"] for source in results} == {"TB Specimen Bank", "KMRC"}


def test_distribution_source_category_filter_is_respected():
    results = filter_distribution_sources("", ["해외 공공은행"])
    assert results
    assert all(source["category"] == "해외 공공은행" for source in results)
    assert filter_distribution_sources("", []) == []
