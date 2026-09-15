"""qPCR 교차반응 검토용 기본 후보 데이터.

아래 목록은 시험 설계를 시작하기 위한 참고 패널이며, 특정 키트의 성능을
보증하거나 규제기관의 필수 패널을 대체하지 않는다.
"""

from __future__ import annotations

import re


TARGET_ALIASES = {
    "stec": ("stec", "ehec", "shiga toxin", "시가독소", "장출혈성 대장균",
             "escherichia coli o157", "e. coli o157", "e coli o157"),
    "shigella": ("shigella", "이질균", "세균성 이질"),
    "salmonella": ("salmonella", "살모넬라"),
    "campylobacter": ("campylobacter", "campylobacter jejuni", "c. jejuni", "c jejuni",
                       "캄필로박터"),
    "c_difficile": ("clostridioides difficile", "clostridium difficile", "c. difficile", "c difficile",
                     "cdiff", "클로스트리디오이데스"),
    "listeria": ("listeria monocytogenes", "l. monocytogenes", "l monocytogenes",
                  "listeria", "리스테리아 모노사이토제네스",
                  "리스테리아"),
    "norovirus": ("norovirus", "noro", "노로바이러스"),
    "rotavirus": ("rotavirus", "로타바이러스"),
    "sars_cov_2": ("sars-cov-2", "sars cov 2", "covid", "2019-ncov", "코로나19"),
    "influenza": ("influenza", "인플루엔자", "독감"),
    "rsv": ("respiratory syncytial", "rsv", "호흡기세포융합"),
    "pertussis": ("bordetella pertussis", "b. pertussis", "b pertussis", "백일해"),
    "m_pneumoniae": ("mycoplasma pneumoniae", "m. pneumoniae", "m pneumoniae",
                      "마이코플라스마 폐렴"),
    "malaria": ("plasmodium", "plasmodium falciparum",
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

# 유전자명만 입력되었을 때의 병원체 범위는 검증 논문에 근거해 별도로
# 관리한다. 같은 유전자라도 primer/probe 위치에 따라 종 특이성이 달라질
# 수 있으므로, 서열 정보가 없는 입력은 논문이 지지하는 보수적인 양성
# 범위(genus 수준)로 해석한다.
TARGET_GENE_EVIDENCE = {
    "stx1": {
        "aliases": ("stx1", "stx 1"), "target_id": "stec", "gene": "stx1",
        "organism": "STEC/EHEC", "canonical": "STEC/EHEC",
        "positive_taxa": ("stec", "ehec", "escherichia coli o157"), "auto_classify": True,
        "summary": "Shiga toxin-producing E. coli의 독소 유전자 표적",
        "source": "Perelle et al., 2004", "url": "https://pubmed.ncbi.nlm.nih.gov/16271448/",
    },
    "stx2": {
        "aliases": ("stx2", "stx 2"), "target_id": "stec", "gene": "stx2",
        "organism": "STEC/EHEC", "canonical": "STEC/EHEC",
        "positive_taxa": ("stec", "ehec", "escherichia coli o157"), "auto_classify": True,
        "summary": "Shiga toxin-producing E. coli의 독소 유전자 표적",
        "source": "Perelle et al., 2004", "url": "https://pubmed.ncbi.nlm.nih.gov/16271448/",
    },
    "ipah": {
        "aliases": ("ipah", "ipa h"), "target_id": "shigella", "gene": "ipaH",
        "organism": "Shigella spp. / EIEC", "canonical": "Shigella/EIEC",
        "positive_taxa": ("shigella", "enteroinvasive escherichia coli", "eiec"), "auto_classify": True,
        "summary": "Shigella와 장침입성 대장균(EIEC)에 존재하여 둘을 단독으로 구분하지 못함",
        "source": "Vu et al., 2004", "url": "https://pubmed.ncbi.nlm.nih.gov/15583323/",
    },
    "inva": {
        "aliases": ("inva", "inv a"),
        "target_id": "salmonella",
        "gene": "invA",
        "organism": "Salmonella spp.",
        "canonical": "Salmonella",
        "positive_taxa": ("salmonella",),
        "auto_classify": True,
        "summary": "Salmonella 여러 종·아종·혈청형을 포괄하는 침입 유전자 표적",
        "source": "Rahn et al., 1992",
        "url": "https://pubmed.ncbi.nlm.nih.gov/1528198/",
    },
    "ttr": {
        "aliases": ("ttr", "ttrrsbca"), "target_id": "salmonella", "gene": "ttr",
        "organism": "Salmonella spp.", "canonical": "Salmonella",
        "positive_taxa": ("salmonella",), "auto_classify": True,
        "summary": "Salmonella의 tetrathionate respiration 유전자좌를 이용한 검출 표적",
        "source": "Malorny et al., 2004", "url": "https://pubmed.ncbi.nlm.nih.gov/15574899/",
    },
    "mapa": {
        "aliases": ("mapa", "map a"), "target_id": "campylobacter", "gene": "mapA",
        "organism": "Campylobacter jejuni", "canonical": "Campylobacter jejuni",
        "positive_taxa": ("campylobacter jejuni",), "auto_classify": True,
        "summary": "C. jejuni 동정에 사용되는 membrane-associated protein 표적",
        "source": "Stucki et al., 1995", "url": "https://pubmed.ncbi.nlm.nih.gov/7790451/",
    },
    "cadf": {
        "aliases": ("cadf", "cad f"), "target_id": "campylobacter", "gene": "cadF",
        "organism": "Campylobacter spp.", "canonical": "Campylobacter",
        "positive_taxa": ("campylobacter",), "auto_classify": True,
        "summary": "Campylobacter 부착 유전자이며 primer에 따라 C. jejuni/C. coli 범위가 달라짐",
        "source": "Nayak et al., 2016", "url": "https://pubmed.ncbi.nlm.nih.gov/27127589/",
    },
    "tcda": {
        "aliases": ("tcda", "tcd a"), "target_id": "c_difficile", "gene": "tcdA",
        "organism": "toxigenic C. difficile", "canonical": "Clostridioides difficile",
        "positive_taxa": ("clostridioides difficile", "clostridium difficile"), "auto_classify": True,
        "summary": "독소 A 유전자로 독소생성 C. difficile 판별에 사용",
        "source": "Belanger et al., 2003", "url": "https://pubmed.ncbi.nlm.nih.gov/12574274/",
    },
    "tcdb": {
        "aliases": ("tcdb", "tcd b"), "target_id": "c_difficile", "gene": "tcdB",
        "organism": "toxigenic C. difficile", "canonical": "Clostridioides difficile",
        "positive_taxa": ("clostridioides difficile", "clostridium difficile"), "auto_classify": True,
        "summary": "독소 B 유전자로 독소생성 C. difficile 판별에 사용",
        "source": "Belanger et al., 2003", "url": "https://pubmed.ncbi.nlm.nih.gov/12574274/",
    },
    "iap": {
        "aliases": ("iap",),
        "target_id": "listeria",
        "gene": "iap",
        "organism": "Listeria spp.",
        "canonical": "Listeria",
        "positive_taxa": ("listeria",),
        "auto_classify": True,
        "summary": "Listeria 속 공통 p60 유전자이며 primer 위치에 따라 종 구분 가능",
        "source": "Bubert et al., 1992",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC195830/",
    },
    "prfa": {
        "aliases": ("prfa", "prf a"), "target_id": "listeria", "gene": "prfA",
        "organism": "Listeria monocytogenes", "canonical": "Listeria monocytogenes",
        "positive_taxa": ("listeria monocytogenes",), "auto_classify": True,
        "summary": "L. monocytogenes 검출용 병원성 조절 유전자 표적",
        "source": "Rossmanith et al., 2006", "url": "https://pubmed.ncbi.nlm.nih.gov/16814987/",
    },
    "nsp3": {
        "aliases": ("nsp3", "nsp 3"), "target_id": "rotavirus", "gene": "NSP3",
        "organism": "Rotavirus A", "canonical": "Rotavirus A",
        "positive_taxa": ("rotavirus a",), "auto_classify": True,
        "summary": "사람 Rotavirus A 정량 RT-PCR에 검증된 표적",
        "source": "Pang et al., 2004", "url": "https://pubmed.ncbi.nlm.nih.gov/14748075/",
    },
    "vp6": {
        "aliases": ("vp6", "vp 6"), "target_id": "rotavirus", "gene": "VP6",
        "organism": "Rotavirus spp.", "canonical": "Rotavirus",
        "positive_taxa": ("rotavirus",), "auto_classify": True,
        "summary": "Rotavirus group/species 검출에 사용되며 assay 설계에 따라 범위가 달라짐",
        "source": "Joshi et al., 2019", "url": "https://pubmed.ncbi.nlm.nih.gov/30710566/",
    },
    "ptxs1": {
        "aliases": ("ptxs1", "ptx s1"), "target_id": "pertussis", "gene": "ptxS1",
        "organism": "Bordetella pertussis", "canonical": "Bordetella pertussis",
        "positive_taxa": ("bordetella pertussis",), "auto_classify": True,
        "summary": "다중 표적 PCR에서 B. pertussis 확인 표적으로 사용",
        "source": "Tatti et al., 2011", "url": "https://pubmed.ncbi.nlm.nih.gov/24131698/",
    },
}

# 아래 표적명은 여러 병원체·생물군에서 쓰이거나 primer 위치에 따라 범위가
# 크게 달라 단독 입력만으로는 안전하게 분류하지 않는다.
AMBIGUOUS_GENE_EVIDENCE = {
    "hlya": {"aliases": ("hlya", "hly a"), "gene": "hlyA", "summary": "여러 세균의 hemolysin 유전자명으로 사용됨"},
    "is481": {"aliases": ("is481", "is 481"), "gene": "IS481", "summary": "B. pertussis뿐 아니라 B. holmesii 등에서도 검출 가능"},
    "rdrp": {"aliases": ("rdrp", "rna dependent rna polymerase"), "gene": "RdRp", "summary": "다양한 RNA 바이러스가 공유하는 중합효소 표적"},
    "matrix": {"aliases": ("matrix gene", "m gene"), "gene": "M gene", "summary": "여러 바이러스의 matrix 유전자에 쓰이는 일반명"},
    "orf": {"aliases": ("orf1", "orf2", "orf 1", "orf 2"), "gene": "ORF1/ORF2", "summary": "다양한 병원체에서 쓰이는 일반 ORF 명칭"},
    "p1": {"aliases": ("p1", "p1 gene"), "gene": "P1", "summary": "여러 생물에서 쓰이는 짧고 비고유한 유전자명"},
    "18s": {"aliases": ("18s rrna", "18s rRNA", "18s"), "gene": "18S rRNA", "summary": "진핵생물 전반에 존재하며 primer 서열로 범위가 결정됨"},
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


def gene_evidence_for_query(query: str) -> tuple[dict, ...]:
    """입력에서 문헌으로 검증된 표적 유전자 프로필을 반환한다."""
    text = (query or "").strip().lower()
    return tuple(
        profile for profile in TARGET_GENE_EVIDENCE.values()
        if any(_contains_term(text, alias) for alias in profile["aliases"])
    )


def gene_evidence_for_queries(queries) -> tuple[dict, ...]:
    """여러 입력의 유전자 근거를 중복 없이 입력 순서대로 반환한다."""
    output = []
    seen = set()
    for query in queries:
        for profile in gene_evidence_for_query(query):
            if profile["gene"].casefold() in seen:
                continue
            seen.add(profile["gene"].casefold())
            output.append(profile)
    return tuple(output)


def ambiguous_gene_evidence_for_query(query: str) -> tuple[dict, ...]:
    """병원체 맥락 없이 자동 분류하면 위험한 일반 표적명을 반환한다."""
    text = (query or "").strip().lower()
    return tuple(
        profile for profile in AMBIGUOUS_GENE_EVIDENCE.values()
        if any(_contains_term(text, alias) for alias in profile["aliases"])
    )


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
    gene_profiles = gene_evidence_for_query(query)
    target_ids.update(profile["target_id"] for profile in gene_profiles if profile.get("auto_classify"))

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
        if gene_profiles:
            labels = ", ".join(
                f"{profile['gene']} → {profile['organism']}" for profile in gene_profiles
            )
        else:
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
