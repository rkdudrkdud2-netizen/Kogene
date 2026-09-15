"""미생물·바이러스 표준물질 및 검체 분양처 안내 데이터."""

from __future__ import annotations


DISTRIBUTION_SOURCES = (
    {
        "name": "고려대 병원성바이러스은행",
        "acronym": "KBPV",
        "category": "국내 공공·연구은행",
        "description": "질병관리청 바이러스병원체자원전문은행(고려대) 소개·분양기관 안내",
        "url": "https://nccp.kdca.go.kr/main.do?menu_id=030300",
    },
    {
        "name": "국립마산병원 결핵검체은행",
        "acronym": "TB Specimen Bank",
        "category": "국내 공공·연구은행",
        "description": "결핵 관련 객담·혈액·소변·균주 등 검체 분양 절차·수수료 안내",
        "url": "https://www.mnth.go.kr/html/content.do?depth=cr&menu_cd=04_03_02",
    },
    {
        "name": "대한결핵협회 결핵연구원·한국항산균자원센터",
        "acronym": "KMRC",
        "category": "국내 공공·연구은행",
        "description": "결핵연구원과 한국항산균자원센터 운영·연구자원 안내",
        "url": "https://www.knta.or.kr/_pages/about_us/researcher.asp",
    },
    {
        "name": "국가병원체자원은행",
        "acronym": "NCCP",
        "category": "국내 공공·연구은행",
        "description": "질병관리청 병원체자원 검색·분양 품목 안내",
        "url": "https://nccp.kdca.go.kr/main.do?menu_id=010100",
    },
    {
        "name": "한국수의유전자원은행",
        "acronym": "KVCC",
        "category": "국내 공공·연구은행",
        "description": "농림축산검역본부 수의 미생물·유전자원 안내",
        "url": "https://www.kahis.go.kr/",
    },
    {
        "name": "생물자원센터",
        "acronym": "KCTC",
        "category": "국내 공공·연구은행",
        "description": "Korean Collection for Type Cultures 일반 분양 안내",
        "url": "https://kctc.kribb.re.kr/access/dist/normalDist",
    },
    {
        "name": "한국미생물보존센터",
        "acronym": "KCCM",
        "category": "국내 공공·연구은행",
        "description": "Korean Culture Center of Microorganisms 미생물자원 검색·분양",
        "url": "https://patent.kccm.or.kr/",
    },
    {
        "name": "국립농업과학원 미생물은행",
        "acronym": "KACC",
        "category": "국내 공공·연구은행",
        "description": "농업미생물자원 검색 및 일반·산업용 분양 안내",
        "url": "https://genebank.rda.go.kr/microbeMain.do",
    },
    {
        "name": "체외진단의료기기 표준품 분양",
        "acronym": "MFDS · NIFDS",
        "category": "국내 공공·연구은행",
        "description": "식품의약품안전평가원 표준품 분양 흐름도·분야별 목록 안내",
        "url": "https://nifds.go.kr/wpge/m_433/cont_02/cont_02_03_01.do",
    },
    {
        "name": "항생제내성균주은행",
        "acronym": "CCARM",
        "category": "국내 공공·연구은행",
        "description": "항생제 내성 미생물자원 검색 및 분양 안내",
        "url": "http://knrrb.ccarm-bio.or.kr/index.jsp?rrb=ccarm",
    },
    {
        "name": "Microbe Division",
        "acronym": "JCM · RIKEN BRC",
        "category": "해외 공공은행",
        "description": "Japan Collection of Microorganisms 균주 주문 및 MTA 안내",
        "url": "https://jcm.brc.riken.jp/en/ordering_e",
    },
    {
        "name": "European Virus Archive",
        "acronym": "EVAg",
        "category": "해외 공공은행",
        "description": "바이러스 및 관련 연구자원 검색·주문 안내",
        "url": "https://www.european-virus-archive.com/",
    },
    {
        "name": "American Type Culture Collection",
        "acronym": "ATCC",
        "category": "해외·상업 분양처",
        "description": "글로벌 생물자원 검색 및 주문",
        "url": "https://www.atcc.org/",
        "contact": "국내 공급처 확인: ATCC 국가별 공식 조회",
        "contact_url": "https://www.atcc.org/support/determine-your-distributor",
    },
    {
        "name": "Vircell",
        "acronym": "Vircell",
        "category": "해외·상업 분양처",
        "description": "감염성 질환 진단용 항원·대조물질 제품 안내",
        "url": "https://www.vircell.com/",
        "contact": "국내 공급 문의: 나루다이텍",
        "contact_url": "http://www.narootech.co.kr/",
    },
    {
        "name": "Innovative Research",
        "acronym": "Innovative Research",
        "category": "해외·상업 분양처",
        "description": "생물학적 연구 검체 및 표준물질 제품 검색",
        "url": "https://www.innov-research.com/",
    },
)

CATEGORIES = tuple(dict.fromkeys(source["category"] for source in DISTRIBUTION_SOURCES))


def filter_distribution_sources(query: str = "", categories=None) -> list[dict]:
    """기관명·약어·설명·분류를 기준으로 분양처를 필터링한다."""
    term = (query or "").strip().casefold()
    selected = set(CATEGORIES if categories is None else categories)
    return [
        dict(source)
        for source in DISTRIBUTION_SOURCES
        if source["category"] in selected
        and (not term or term in " ".join(str(value) for value in source.values()).casefold())
    ]
