from reference_lookup import resolve_from_articles


def test_two_independent_titles_can_resolve_a_supported_pathogen():
    result = resolve_from_articles("novelTarget", [
        {"pmid": "1", "title": "novelTarget qPCR detection of Salmonella enterica"},
        {"pmid": "2", "title": "Evaluation of novelTarget PCR for Salmonella"},
        {"pmid": "3", "title": "Unrelated assay in Listeria"},
    ])
    assert result["status"] == "resolved"
    assert result["organism"] == "Salmonella"
    assert result["support_count"] == 2


def test_competing_literature_is_not_auto_classified():
    result = resolve_from_articles("sharedGene", [
        {"pmid": "1", "title": "sharedGene PCR in Salmonella"},
        {"pmid": "2", "title": "sharedGene qPCR in Salmonella"},
        {"pmid": "3", "title": "sharedGene PCR in Listeria"},
        {"pmid": "4", "title": "sharedGene qPCR in Listeria"},
    ])
    assert result["status"] == "ambiguous"


def test_one_paper_is_not_enough_to_auto_classify():
    result = resolve_from_articles("rareGene", [
        {"pmid": "1", "title": "rareGene qPCR in Campylobacter jejuni"},
    ])
    assert result["status"] == "insufficient"
