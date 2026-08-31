from __future__ import annotations

import html
import importlib

import pandas as pd
import streamlit as st

import cross_reactivity_data
import candidate_grouping
import excel_reporting
import specificity_engine
import worklist
from distribution_sources import CATEGORIES, DISTRIBUTION_SOURCES, filter_distribution_sources
from inventory_matching import find_matches, normalize_name, read_inventory


# 장시간 실행 중인 Streamlit 서버에서도 검색 데이터·규칙 변경을 즉시 반영한다.
cross_reactivity_data = importlib.reload(cross_reactivity_data)
candidate_grouping = importlib.reload(candidate_grouping)
excel_reporting = importlib.reload(excel_reporting)
specificity_engine = importlib.reload(specificity_engine)
worklist = importlib.reload(worklist)


st.set_page_config(page_title="qPCR CrossCheck", page_icon="🧬", layout="wide")

st.markdown("""
<style>
  :root {--navy:#17324d; --teal:#0f766e; --teal-soft:#ccfbf1; --amber:#b45309;
    --amber-soft:#fef3c7; --slate:#475569; --slate-soft:#f1f5f9; --line:#dbe3ee;}
  html, body, [class*="css"], .stApp {font-family:"Segoe UI","Noto Sans KR","Malgun Gothic",sans-serif;}
  .stApp {background: #f5f7fb; color: #172033; font-size:15px; line-height:1.55;}
  .block-container {max-width: 1480px; padding-top: 1.65rem; padding-bottom: 4rem;}
  h1, h2, h3 {font-family:"Segoe UI","Noto Sans KR","Malgun Gothic",sans-serif;
    letter-spacing:-.025em; color:#102a43;}
  h2 {font-size:1.65rem !important;} h3 {font-size:1.35rem !important;}
  [data-testid="stSidebar"] {background: #172235; border-right:0;}
  [data-testid="stSidebar"] * {color: #e5edf7;}
  [data-testid="stSidebar"] label, [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] small {color:#e5edf7 !important;}
  [data-testid="stSidebar"] input {color:#111827 !important; background:#ffffff !important;}
  [data-testid="stSidebar"] [data-baseweb="select"] * {color:#111827 !important;}
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background:#223149; border-color:#52627a;
  }
  [data-testid="stSidebar"] hr {border-color:#334155;}
  .sidebar-brand {padding:.4rem .2rem 1.15rem; border-bottom:1px solid #334155; margin-bottom:.9rem;}
  .sidebar-brand .mark {display:inline-flex; width:34px; height:34px; align-items:center;
    justify-content:center; margin-right:.6rem; border:1px solid #64748b; border-radius:8px;
    color:#67e8f9; font-weight:900; vertical-align:middle;}
  .sidebar-brand strong {font-size:1rem; letter-spacing:.12em; color:#ffffff;}
  .sidebar-brand small {display:block; margin:.4rem 0 0 3rem; color:#8fa3bf !important;
    font-size:.66rem; letter-spacing:.08em;}
  [data-testid="stSidebar"] [role="radiogroup"] label {padding:.45rem .55rem; border-radius:9px;}
  [data-testid="stSidebar"] [role="radiogroup"] label:hover {background:#25354f;}
  .hero {background: linear-gradient(125deg,#102a43 0%,#155e75 68%,#0f766e 100%); color:white;
         padding:1.75rem 2rem; border-radius:20px; margin-bottom:1.15rem;
         box-shadow:0 14px 34px rgba(15,43,68,.14); border:1px solid rgba(255,255,255,.08);}
  .hero .eyebrow {font-size:.78rem; letter-spacing:.13em; font-weight:800; color:#67e8f9;}
  .hero h1 {font-size:2.2rem; line-height:1.12; margin:.4rem 0 .5rem; color:white; letter-spacing:-.035em;}
  .hero p {max-width:820px; color:#dbeafe; margin:0; font-size:.96rem; line-height:1.65;}
  [data-testid="stMetric"] {background:white; border:1px solid #e2e8f0; border-radius:16px;
    padding:.85rem 1rem; text-align:center; min-height:102px; display:flex; flex-direction:column;
    align-items:center; justify-content:center; box-shadow:0 5px 18px rgba(15,23,42,.04);}
  [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {width:100%; justify-content:center;}
  [data-testid="stMetricLabel"] > div {justify-content:center; width:100%;}
  [data-testid="stMetricLabel"] p {font-size:.76rem !important; color:#64748b !important; font-weight:700;}
  [data-testid="stMetricValue"] {font-size:1.75rem !important; color:#102a43 !important; letter-spacing:-.04em;}
  .section-label {font-size:.74rem; color:#0f766e; font-weight:800; letter-spacing:.11em; margin-top:1.65rem;}
  .footer-note {border-left:3px solid #06b6d4; padding:.1rem 0 .1rem 1rem; color:#64748b; font-size:.88rem;}
  .validation-summary {background:#fff; border:1px solid var(--line); border-radius:17px; padding:1rem 1.15rem;
    box-shadow:0 6px 20px rgba(15,23,42,.045); min-height:132px; margin:.25rem 0 .75rem;}
  .validation-summary.inclusivity {border-top:4px solid #0f766e;}
  .validation-summary.specificity {border-top:4px solid #155e75;}
  .validation-summary .summary-kicker {font-size:.7rem; font-weight:800; letter-spacing:.1em; color:#64748b;}
  .validation-summary .summary-row {display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; margin:.3rem 0 .65rem;}
  .validation-summary .summary-title {font-size:1.05rem; font-weight:800; color:#17324d;}
  .validation-summary .summary-total {font-size:1.8rem; line-height:1; font-weight:800; color:#0f766e; letter-spacing:-.04em;}
  .priority-chips {display:flex; flex-wrap:wrap; gap:.38rem;}
  .priority-chip {display:inline-flex; align-items:center; padding:.24rem .55rem; border-radius:999px;
    font-size:.74rem; font-weight:800;}
  .priority-chip.required {background:var(--teal-soft); color:#115e59;}
  .priority-chip.recommended {background:var(--amber-soft); color:#92400e;}
  .priority-chip.reference {background:var(--slate-soft); color:#475569;}
  [data-testid="stDataFrame"] {border:1px solid var(--line); border-radius:14px; overflow:hidden;
    box-shadow:0 4px 14px rgba(15,23,42,.035);}
  [data-testid="stSegmentedControl"] {margin:.05rem 0 .45rem;}
  [data-testid="stSegmentedControl"] button {font-size:.82rem; font-weight:750; border-radius:9px;}
  [data-testid="stExpander"] {border:1px solid var(--line) !important; border-radius:12px !important;
    background:#fff;}
  [data-baseweb="tab-list"] {gap:.35rem; background:#eaf0f6; padding:.3rem; border-radius:12px;}
  [data-baseweb="tab"] {height:2.5rem; border-radius:9px; padding:0 .9rem; font-size:.86rem; font-weight:750;}
  [aria-selected="true"][data-baseweb="tab"] {background:#fff; color:#0f766e;
    box-shadow:0 2px 8px rgba(15,23,42,.08);}
  [data-testid="stAlert"] {border-radius:13px; border-width:1px; font-size:.9rem;}
  .stCaptionContainer, [data-testid="stCaptionContainer"] {color:#64748b; font-size:.83rem;}
  button[kind="primary"], button[kind="secondary"] {border-radius:10px; font-weight:700;}
  .source-card {background:#ffffff; border:1px solid #dbe3ee; border-radius:16px; padding:1.15rem;
    min-height:272px; margin-bottom:1rem; box-shadow:0 7px 22px rgba(15,23,42,.05);
    display:flex; flex-direction:column;}
  .source-card .source-badge {display:inline-block; align-self:flex-start; border-radius:999px;
    background:#e6f7fb; color:#0e7490; padding:.25rem .58rem; font-size:.72rem; font-weight:800;}
  .source-card h3 {color:#132238; font-size:1.08rem; line-height:1.35; margin:1rem 0 .25rem;}
  .source-card .source-acronym {color:#0e7490; font-size:.8rem; font-weight:800; letter-spacing:.04em;}
  .source-card .source-description {color:#64748b; font-size:.88rem; line-height:1.55;
    margin:.85rem 0 1rem; flex:1;}
  .source-card .source-link {display:block; text-align:center; padding:.58rem .7rem; border-radius:9px;
    background:#155e75; color:#ffffff !important; font-weight:800; text-decoration:none;}
  .source-card .source-link:hover {background:#0e7490;}
  .source-card .source-contact {color:#475569; font-size:.76rem; line-height:1.45; margin-top:.7rem; text-align:center;}
  .source-card .source-contact a {color:#0e7490; font-weight:700;}
</style>
""", unsafe_allow_html=True)

def build_results(rows, inventory, threshold):
    results = []
    for item in rows:
        matches, match = find_matches(item["organism"], item["aliases"], inventory, threshold)
        management_ids = [entry.inventory_id for entry in matches if entry.inventory_id]
        inventory_names = [entry.inventory_name for entry in matches if entry.inventory_name]
        catalog_numbers = [entry.catalog_no for entry in matches if entry.catalog_no]
        source_sheets = [entry.sheet for entry in matches if entry.sheet]
        results.append({
            **item, "보유 여부": "보유" if matches else "미보유", "보유 자원 수": len(matches),
            "매칭 점수": match.score,
            "자원 상세": matches,
            "관리번호": ", ".join(dict.fromkeys(management_ids)) if management_ids else "—",
            "사내 매칭명": "; ".join(dict.fromkeys(inventory_names)) if inventory_names else (match.inventory_name or "—"),
            "Cat no.": ", ".join(dict.fromkeys(catalog_numbers)) if catalog_numbers else "—",
            "매칭 방식": match.method,
            "원본 시트": ", ".join(dict.fromkeys(source_sheets)) if source_sheets else "—",
        })
    return results


def render_distribution_page():
    """표준물질·검체 분양처를 검색 가능한 카드 목록으로 표시한다."""
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">RESOURCE DIRECTORY · ORDERING LINKS</div>
      <h1>미생물·바이러스 분양처 안내</h1>
      <p>국내외 균주은행, 병원체자원은행과 표준물질 공급처를 한 화면에서 검색하고 공식 안내 페이지로 이동합니다.</p>
    </div>
    """, unsafe_allow_html=True)

    filters = st.columns([1.45, 1])
    with filters[0]:
        source_query = st.text_input(
            "분양처 검색", placeholder="기관명, 약어, 자원 종류를 입력하세요. 예: 결핵, ATCC, 바이러스",
            key="distribution_query",
        )
    with filters[1]:
        selected_categories = st.multiselect(
            "기관 분류", CATEGORIES, default=list(CATEGORIES), key="distribution_categories",
        )

    sources = filter_distribution_sources(source_query, selected_categories)
    source_metrics = st.columns(3)
    source_metrics[0].metric("등록 분양처", f"{len(DISTRIBUTION_SOURCES)}곳")
    source_metrics[1].metric("현재 검색 결과", f"{len(sources)}곳")
    source_metrics[2].metric("기관 분류", f"{len(CATEGORIES)}개")

    st.markdown('<div class="section-label">RESOURCE DIRECTORY</div>', unsafe_allow_html=True)
    st.subheader("기관별 분양·주문 안내")
    st.caption(
        "기관명을 검색하거나 분류를 선택하면 필요한 공급처를 빠르게 좁힐 수 있습니다. "
        "링크와 기관 정보는 2026-08-24 기준으로 재확인했습니다."
    )
    if not sources:
        st.warning("현재 조건과 일치하는 분양처가 없습니다. 검색어 또는 기관 분류를 조정해 주세요.")
    else:
        card_columns = st.columns(3)
        for index, source in enumerate(sources):
            name = html.escape(source["name"])
            acronym = html.escape(source["acronym"])
            category = html.escape(source["category"])
            description = html.escape(source["description"])
            url = html.escape(source["url"], quote=True)
            contact = ""
            if source.get("contact"):
                contact_text = html.escape(source["contact"])
                contact_url = html.escape(source.get("contact_url", source["url"]), quote=True)
                contact = (
                    f'<div class="source-contact"><a href="{contact_url}" target="_blank" '
                    f'rel="noopener noreferrer">{contact_text}</a></div>'
                )
            with card_columns[index % 3]:
                st.markdown(
                    f"""
                    <div class="source-card">
                      <span class="source-badge">{category}</span>
                      <h3>{name}</h3>
                      <div class="source-acronym">{acronym}</div>
                      <div class="source-description">{description}</div>
                      <a class="source-link" href="{url}" target="_blank" rel="noopener noreferrer">공식 페이지 열기 ↗</a>
                      {contact}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.info("분양 가능 품목, 생물안전등급, MTA, 운송·수입 요건과 최신 비용은 주문 전에 각 기관에서 확인해 주세요.")


with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
      <span class="mark">Q</span><strong>QPCR CROSSCHECK</strong>
      <small>MOLECULAR QC WORKSPACE</small>
    </div>
    """, unsafe_allow_html=True)
    page = st.radio("WORKSPACE", ("교차검증 패널", "분양처 안내"), index=0)
    st.markdown("---")

if page == "분양처 안내":
    render_distribution_page()
    st.stop()

with st.sidebar:
    st.markdown("### 검색 설정")
    assay_type = st.selectbox(
        "qPCR 구성", ("Single qPCR", "Multiplex qPCR"), index=1,
        help="Single과 Multiplex 모두 같은 교차검증·자원 작업 목록을 사용합니다.",
    )
    target_queries = []
    if assay_type == "Multiplex qPCR":
        target_count = int(st.number_input(
            "타겟 수", min_value=1, max_value=20, value=2, step=1,
            help="입력한 수만큼 질환·병원체·표적 유전자 입력란이 생성됩니다.",
        ))
        for index in range(target_count):
            target_queries.append(st.text_input(
                f"질환 / 표적 유전자 {index + 1}",
                value="장관계 감염증" if index == 0 else "",
                placeholder="예: Malaria, Salmonella, stx1/stx2",
                key=f"multiplex_target_{index + 1}",
            ))
    else:
        target_queries.append(st.text_input(
            "질환 / 표적 유전자",
            value="장관계 감염증",
            placeholder="예: Salmonella 또는 invA",
            key="single_target",
        ))
    target = " + ".join(value.strip() for value in target_queries if value.strip())
    threshold = st.slider(
        "보유 판정 유사도", 70, 100, 86,
        help="값이 낮으면 표기 차이를 넓게 잡지만 오매칭 가능성이 커집니다.",
    )
    st.markdown("---")
    st.markdown("### 사내 자원 대조")
    inventory_file = st.file_uploader(
        "보유 미생물 파일", type=["csv", "xlsx", "xlsm"],
        help="파일은 서버에 저장하지 않으며, 새 세션마다 다시 업로드해야 합니다.",
    )
    st.caption("균주명·미생물명·Organism 열을 자동으로 찾습니다. 여러 Excel 시트와 상단 설명행도 지원합니다.")

st.markdown("""
<div class="hero">
  <div class="eyebrow">MOLECULAR DIAGNOSTICS · QC PLANNING</div>
  <h1>qPCR CrossCheck</h1>
  <p>진단 표적별 교차반응 검토 후보를 분류하고, 사내 보유 자원과 이름을 지능적으로 대조합니다.</p>
</div>
""", unsafe_allow_html=True)

inventory, inventory_error = None, None
if inventory_file is not None:
    try:
        inventory = read_inventory(inventory_file)
    except Exception as exc:
        inventory_error = str(exc)

if inventory_error:
    st.error(f"재고 파일 처리 실패: {inventory_error}")
elif inventory is not None:
    normalized_names = inventory["inventory_name"].map(normalize_name)
    unique_name_count = normalized_names[normalized_names != ""].nunique()
    valid_name_count = int((normalized_names != "").sum())
    duplicate_row_count = valid_name_count - unique_name_count
    st.success(
        f"업로드 완료 · 자원 레코드 {len(inventory):,}건 · "
        f"정규화 이름 {unique_name_count:,}개 · 동일 이름 반복 {duplicate_row_count:,}건"
    )
else:
    st.info("사내 자원 파일을 업로드하면 보유 여부와 최적 매칭명을 표시합니다. 지금은 모든 후보를 미보유로 표시합니다.")

specificity_rows, interpretation, unrecognized_targets = cross_reactivity_data.select_cross_reactivity_rows_for_targets(target_queries)
specificity_rows, inventory_resolved_targets = specificity_engine.augment_rows_from_inventory(
    specificity_rows, target_queries, inventory,
)
inclusivity_rows = specificity_engine.build_inclusivity_rows(target_queries, inventory)
specificity_rows = specificity_engine.exclude_inclusivity_from_specificity(
    specificity_rows, inclusivity_rows,
)
specificity_rows = specificity_engine.assign_specificity_metadata(specificity_rows)
unrecognized_targets = [
    target for target in unrecognized_targets
    if target.casefold() not in inventory_resolved_targets
]
if inventory_resolved_targets:
    interpretation = interpretation.replace(" · 자동 분류 필요", " · 사내 자원 기반 자동 분류")
    interpretation += f" · 사내 자원 기반 특이도 후보 확장 {len(inventory_resolved_targets)}개 타겟"
inclusivity_results = build_results(inclusivity_rows, inventory, threshold)
specificity_results = build_results(specificity_rows, inventory, threshold)
results = [*inclusivity_results, *specificity_results]
owned_count = sum(item["보유 여부"] == "보유" for item in results)
missing_count = len(results) - owned_count
matched_resource_count = sum(item["보유 자원 수"] for item in results)
inventory_count = len(inventory) if inventory is not None else 0
direct_count = sum(item.get("scope") == "표적 직접 연관" for item in results)
expanded_count = sum(item.get("scope") == "증후군 확장" for item in results)
inventory_related_count = sum(item.get("scope") == "재고 기반 근연 후보" for item in results)
inventory_syndrome_count = sum(item.get("scope") == "재고 기반 증후군 후보" for item in results)

metrics = st.columns(4)
metrics[0].metric("업로드 자원", f"{inventory_count}건")
metrics[1].metric("보유 후보종", f"{owned_count}종")
metrics[2].metric("매칭 자원", f"{matched_resource_count}건")
metrics[3].metric("미보유 후보종", f"{missing_count}종")

summary_columns = st.columns(2)
with summary_columns[0]:
    st.markdown(
        f"""
        <div class="validation-summary inclusivity">
          <div class="summary-kicker">INCLUSIVITY</div>
          <div class="summary-row"><span class="summary-title">포괄성 후보</span><span class="summary-total">{len(inclusivity_results)}종</span></div>
          <div class="priority-chips">
            <span class="priority-chip required">필수 {sum(item.get('우선순위') == '필수' for item in inclusivity_results)}</span>
            <span class="priority-chip recommended">권장 {sum(item.get('우선순위') == '권장' for item in inclusivity_results)}</span>
            <span class="priority-chip reference">참고 {sum(item.get('우선순위') == '참고' for item in inclusivity_results)}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with summary_columns[1]:
    st.markdown(
        f"""
        <div class="validation-summary specificity">
          <div class="summary-kicker">EXCLUSIVITY · CROSS-REACTIVITY</div>
          <div class="summary-row"><span class="summary-title">특이도 후보</span><span class="summary-total">{len(specificity_results)}종</span></div>
          <div class="priority-chips">
            <span class="priority-chip required">필수 {sum(item.get('우선순위') == '필수' for item in specificity_results)}</span>
            <span class="priority-chip recommended">권장 {sum(item.get('우선순위') == '권장' for item in specificity_results)}</span>
            <span class="priority-chip reference">참고 {sum(item.get('우선순위') == '참고' for item in specificity_results)}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
st.caption(f"검색 해석 · {interpretation}")
if unrecognized_targets:
    st.info(
        "자동 분류가 필요한 사용자 입력 병원체: " + ", ".join(unrecognized_targets)
        + " · 검색과 사내 자원 대조에는 포함했습니다. 분류와 교차반응 후보는 검토 후 보완해 주세요."
    )
if direct_count or expanded_count:
    st.caption(f"패널 구성 · 표적 직접 연관 {direct_count}종 + 같은 증후군 확장 {expanded_count}종")
if inventory_related_count or inventory_syndrome_count:
    st.caption(
        f"사내 자원 확장 · 같은 속·바이러스군 {inventory_related_count}종"
        f" + 동일 증후군·검체 범주 {inventory_syndrome_count}종"
    )
st.info("포괄성 목록은 타겟 자체와 동일 종·strain·형을, 특이도 목록은 근연 비표적종과 동일 증후군·검체 범주의 병원체를 표시합니다. 두 목록 모두 필수·권장·참고 우선순위로 구분합니다.")

worklist_rows = worklist.build_worklist_rows(results, assay_type, target)
st.markdown('<div class="section-label">LAB WORKLIST</div>', unsafe_allow_html=True)
st.subheader(f"{assay_type} 시험 작업 목록")
st.caption("포괄성·특이도 후보의 질환군·병원체 유형과 매칭된 모든 관리번호를 표시합니다. 검증 구분과 시험 우선순위를 유지하며 원액은 µL, 희석액은 튜브 수(n)로 통일합니다.")
show_reference_worklist = st.toggle("작업목록에 참고 후보 포함", value=False, key="show_reference_worklist")
visible_worklist_rows = [
    row for row in worklist_rows if show_reference_worklist or row.get("우선순위") != "참고"
]
ready_count = sum(row["준비 상태"] == "즉시 사용 가능" for row in visible_worklist_rows)
preparation_count = sum(row["준비 상태"] in {"희석 필요", "원액 사용 가능"} for row in visible_worklist_rows)
exhausted_count = sum(row["준비 상태"] in {"소진", "미보유"} for row in visible_worklist_rows)
check_count = sum(
    row["준비 상태"] == "정보 확인 필요" or row["재고 점검"] not in {"정상", "—"}
    for row in visible_worklist_rows
)

if not show_reference_worklist:
    hidden_reference_count = len(worklist_rows) - len(visible_worklist_rows)
    st.caption(f"현재 필수·권장 후보만 표시 중 · 참고 작업 {hidden_reference_count:,}건 숨김")
work_metrics = st.columns(4)
work_metrics[0].metric("즉시 사용 가능", f"{ready_count}건")
work_metrics[1].metric("원액·희석 준비", f"{preparation_count}건")
work_metrics[2].metric("소진·미보유", f"{exhausted_count}건")
work_metrics[3].metric("정보·재고 확인", f"{check_count}건")
st.dataframe(
    pd.DataFrame(visible_worklist_rows), width="stretch", hide_index=True, height=520,
    column_config={
        "qPCR 구성": st.column_config.TextColumn(width="small"),
        "입력 표적": st.column_config.TextColumn(width="medium"),
        "질환군": st.column_config.TextColumn(width="small"),
        "병원체 유형": st.column_config.TextColumn(width="small"),
        "검증 구분": st.column_config.TextColumn(width="small"),
        "우선순위": st.column_config.TextColumn(width="small"),
        "추천 미생물": st.column_config.TextColumn(width="medium"),
        "선정 범위": st.column_config.TextColumn(width="medium"),
        "관리번호": st.column_config.TextColumn(width="small"),
        "사내 자원명": st.column_config.TextColumn(width="large"),
        "최초 원액 용량 (µL)": st.column_config.NumberColumn(format="%.1f"),
        "원액 누적 사용량 (µL)": st.column_config.NumberColumn(format="%.1f"),
        "원액 잔량 (µL)": st.column_config.NumberColumn(format="%.1f"),
        "희석액(1/100) 튜브 수 (n)": st.column_config.NumberColumn(format="%d"),
        "준비 상태": st.column_config.TextColumn(width="medium"),
        "재고 점검": st.column_config.TextColumn(width="medium"),
        "비고": st.column_config.TextColumn(width="large"),
        "매칭 점수": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
    },
)
st.caption(
    "재고 수치 열은 업로드 원본에 숫자로 제공된 값만 표시하며 빈 값이나 ‘소진’을 0으로 임의 변환하지 않습니다. "
    "재고 점검은 수치 3개가 모두 제공된 경우에만 ‘최초 원액 용량 − 누적 사용량 = 원액 잔량’인지 확인합니다. "
    "구매일은 유효기간 판정이 아니라 자원 식별 정보로만 표시합니다."
)

def render_candidate_table(group, table_key, grouped_view=True):
    if not group:
        st.caption("현재 검색 조건에 해당하는 후보가 없습니다.")
        return
    display = pd.DataFrame([{
        "우선순위": item.get("우선순위", "참고"),
        "미생물": item["organism"],
        "관련 입력 표적": " + ".join(item.get("input_targets", (target,))),
        "분류": item["relation"], "선정 범위": item.get("scope", "기본 패널"),
        "검토 근거": item["basis"],
        "보유 여부": item["보유 여부"], "보유 자원 수": item["보유 자원 수"],
        "관리번호": item["관리번호"], "점수": item["매칭 점수"],
        "사내 매칭명": item["사내 매칭명"], "Cat no.": item["Cat no."],
    } for item in group])
    priority_colors = {
        "필수": "background-color:#ccfbf1;color:#115e59;font-weight:700",
        "권장": "background-color:#fef3c7;color:#92400e;font-weight:700",
        "참고": "background-color:#f1f5f9;color:#475569;font-weight:700",
    }
    if grouped_view:
        grouped_rows = candidate_grouping.group_candidate_rows(group)
        core_display = pd.DataFrame(grouped_rows)
        core_columns = ["우선순위", "대표 병원체", "세부 후보 수", "관련 입력 표적", "분류", "보유 여부", "보유 자원 수"]
        core_display = core_display[core_columns]
        st.caption(f"대표 병원체 {len(core_display)}개로 세부 후보 {len(display)}개를 묶어 표시합니다.")
    else:
        core_columns = ["우선순위", "미생물", "관련 입력 표적", "분류", "보유 여부", "보유 자원 수", "관리번호"]
        core_display = display[core_columns]
    core_display = core_display.style.map(lambda value: priority_colors.get(value, ""), subset=["우선순위"])
    st.dataframe(
        core_display, width="stretch", hide_index=True,
        height=min(520, 44 + (len(grouped_rows) if grouped_view else len(display)) * 35),
        column_config={
            "우선순위": st.column_config.TextColumn(width="small"),
            "관련 입력 표적": st.column_config.TextColumn(width="small" if grouped_view else "medium"),
            "미생물": st.column_config.TextColumn(width="large"),
            "대표 병원체": st.column_config.TextColumn(width="medium"),
            "세부 후보 수": st.column_config.NumberColumn("세부 후보", format="%d개", width="small"),
            "분류": st.column_config.TextColumn(width="medium"),
            "관리번호": st.column_config.TextColumn("관리번호", width="medium", help="매칭된 모든 사내 자원의 관리번호"),
            "보유 자원 수": st.column_config.NumberColumn("보유 자원 수", format="%d건"),
        },
    )
    with st.expander(f"세부 후보·근거·매칭 정보 보기 · {len(display)}행", expanded=False):
        st.dataframe(
            display, width="stretch", hide_index=True, height=min(480, 44 + len(display) * 35),
            column_config={
                "우선순위": st.column_config.TextColumn(width="small"),
                "점수": st.column_config.ProgressColumn("매칭 점수", min_value=0, max_value=100, format="%.1f"),
                "관련 입력 표적": st.column_config.TextColumn(width="medium"),
                "선정 범위": st.column_config.TextColumn(width="medium"),
                "검토 근거": st.column_config.TextColumn(width="large"),
                "관리번호": st.column_config.TextColumn("관리번호", width="medium"),
                "보유 자원 수": st.column_config.NumberColumn("보유 자원 수", format="%d건"),
                "사내 매칭명": st.column_config.TextColumn(width="large"),
            },
            key=f"{table_key}_details",
        )


st.markdown('<div class="section-label">VALIDATION PANELS</div>', unsafe_allow_html=True)
st.subheader("포괄성·특이도 검토 후보")
validation_tabs = st.tabs(["포괄성 목록", "특이도 목록"])

with validation_tabs[0]:
    st.caption("타겟 자체와 동일 종·strain·혈청형·유전형의 검출 포괄성을 확인하는 목록입니다.")
    inclusivity_controls = st.columns([1, 1.8])
    with inclusivity_controls[0]:
        show_inclusivity_reference = st.toggle("참고 후보 포함", value=False, key="show_inclusivity_reference")
    with inclusivity_controls[1]:
        inclusivity_view = st.segmented_control(
            "표시 방식", ["대표 병원체 묶음", "세부 후보 전체"], default="대표 병원체 묶음",
            key="inclusivity_view", width="stretch",
        )
    visible_inclusivity = [
        item for item in inclusivity_results if show_inclusivity_reference or item.get("우선순위") != "참고"
    ]
    render_candidate_table(visible_inclusivity, "inclusivity", inclusivity_view == "대표 병원체 묶음")

with validation_tabs[1]:
    st.caption("근연 비표적종과 동일 증후군·검체 범주의 병원체에 대한 교차반응·배제 확인 목록입니다.")
    specificity_controls = st.columns([1, 1.8])
    with specificity_controls[0]:
        show_specificity_reference = st.toggle("참고 후보 포함", value=False, key="show_specificity_reference")
    with specificity_controls[1]:
        specificity_view = st.segmented_control(
            "표시 방식", ["대표 병원체 묶음", "세부 후보 전체"], default="대표 병원체 묶음",
            key="specificity_view", width="stretch",
        )
    visible_specificity = [
        item for item in specificity_results if show_specificity_reference or item.get("우선순위") != "참고"
    ]

    tab_groups = [
        ("장관계 · 세균", "장관계", "세균"),
        ("장관계 · 바이러스", "장관계", "바이러스"),
        ("호흡기계 · 세균", "호흡기계", "세균"),
        ("호흡기계 · 바이러스", "호흡기계", "바이러스"),
        ("혈액매개 · 기생충", "혈액매개", "기생충"),
    ]
    known_groups = {(system, kind) for _, system, kind in tab_groups}
    for item in visible_specificity:
        group_key = (item["system"], item["kind"])
        if group_key not in known_groups:
            tab_groups.append((f"{item['system']} · {item['kind']}", *group_key))
            known_groups.add(group_key)
    specificity_tabs = st.tabs([label for label, _, _ in tab_groups])
    for panel_tab, (_, system, kind) in zip(specificity_tabs, tab_groups):
        with panel_tab:
            render_candidate_table([
                item for item in visible_specificity
                if item["system"] == system and item["kind"] == kind
            ], f"specificity_{system}_{kind}", specificity_view == "대표 병원체 묶음")

st.caption("관리번호는 보유 판정을 받은 후보에 대해 모두 표시됩니다. 미보유 후보는 관리번호가 없어 ‘—’로 표시됩니다.")

st.markdown('<div class="section-label">EXCEL REPORT</div>', unsafe_allow_html=True)
st.subheader("분류별 결과 다운로드")
st.caption("포괄성 후보는 전용 시트에, 특이도 후보는 병원체 분류별 시트에 저장되며 시험 작업목록에는 검증 구분과 우선순위가 함께 표시됩니다.")
st.download_button(
    "결과 Excel 다운로드", excel_reporting.build_excel_download(results, assay_type=assay_type, target=target),
    "qpcr_crosscheck_result.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    width="stretch",
)

st.markdown("""
<div class="footer-note">
이 목록은 시험 설계용 시작점입니다. 최종 패널은 프라이머·프로브 서열의 in-silico 분석,
표적 유행도, 검체 매트릭스, 제품 적용 규정과 위험평가를 반영해 확정하세요.
</div>
""", unsafe_allow_html=True)
