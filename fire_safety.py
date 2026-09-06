# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib3
import urllib.parse
import os
from datetime import datetime

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 페이지 기본 설정
st.set_page_config(page_title="사내 소방안전관리 정보 Dashboard", layout="wide", page_icon="🚒")

# =============================================================
# [모던 디자인 시스템 & 글로벌 CSS 스타일링]
# =============================================================
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif !important;
    }

    /* 배경 및 컨테이너 패딩 */
    .stApp {
        background-color: #f8fafc;
    }
    
    .main .block-container, 
    div[data-testid="stAppViewBlockContainer"] {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1200px !important;
    }

    /* 글로벌 이미지 스타일 */
    img {
        max-width: 100% !important;
        height: auto !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06) !important;
    }

    /* 메인 헤더 배너 */
    .dashboard-header {
        background: linear-gradient(135deg, #1b2a4a 0%, #0f172a 100%);
        padding: 2.2rem 2rem;
        border-radius: 16px;
        color: #ffffff;
        box-shadow: 0 10px 25px -5px rgba(27, 42, 74, 0.25);
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .dashboard-title {
        font-size: clamp(1.6rem, 5vw, 2.3rem) !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
        margin: 0 0 0.5rem 0 !important;
        color: #ffffff !important;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .dashboard-meta {
        font-size: 0.9rem;
        color: #94a3b8;
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 500;
    }
    .dashboard-badge {
        background: rgba(59, 89, 152, 0.25);
        color: #93c5fd;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid rgba(59, 89, 152, 0.4);
    }

    /* 서브헤더 디자인 */
    div[data-testid="stHeading"] h3,
    div[data-testid="stSubheader"] h3 {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        letter-spacing: -0.01em;
        margin-top: 1rem !important;
        margin-bottom: 1rem !important;
    }

    /* 구분선 스타일 */
    hr {
        border-color: #e2e8f0 !important;
        margin: 2rem 0 !important;
    }

    /* Expander 개선 */
    div[data-testid="stExpander"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        background-color: #ffffff !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
        overflow: hidden;
    }
    div[data-testid="stExpander"] > details > summary {
        font-weight: 700 !important;
        color: #1e293b !important;
        padding: 1rem !important;
    }

    /* 탭 스타일 조정 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f1f5f9;
        padding: 5px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        font-size: 0.92rem;
        font-weight: 600;
        color: #64748b;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08) !important;
    }

    /* 본부/반 세부 임무 카드 스타일 */
    .task-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .task-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(0,0,0,0.05);
    }
    .task-card-header {
        font-weight: 700;
        font-size: 1.05rem;
        padding-bottom: 10px;
        margin-bottom: 12px;
        border-bottom: 2px solid;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .task-item {
        margin-bottom: 10px;
        line-height: 1.65;
        font-size: 0.93rem;
        color: #334155;
    }
    .task-item:last-child {
        margin-bottom: 0;
    }

    /* 모바일 반응형 대응 */
    @media (max-width: 768px) {
        .main .block-container,
        div[data-testid="stAppViewBlockContainer"] {
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-top: 1rem !important;
        }

        .dashboard-header {
            padding: 1.5rem 1.2rem;
            border-radius: 12px;
        }

        .timeline-container {
            flex-direction: column !important;
            gap: 12px !important;
        }
        .timeline-line {
            display: none !important;
        }
        .timeline-box {
            width: 100% !important;
            margin-bottom: 0px !important;
            padding: 16px !important;
        }

        .facility-box, .first-aid-box, .dept-card, .night-card {
            padding: 14px !important;
            margin-bottom: 12px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================
# 상단 메인 타이틀
# =============================================================
st.markdown(f"""
    <div class="dashboard-header">
        <div class="dashboard-title">
            <span>🚒</span> 사내 소방안전관리 정보 Dashboard
        </div>
        <div class="dashboard-meta">
            <span class="dashboard-badge">안전환경팀</span>
            <span>최종 업데이트: {datetime.now().strftime('%Y-%m-%d')}</span>
        </div>
    </div>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."

# -------------------------------------------------------------
# 커스텀 표 생성 함수 (반응형 모바일 터치 스크롤 지원)
# -------------------------------------------------------------
def render_centered_table(df, col_widths=None):
    html = """
    <style>
    .centered-table-container {
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin-bottom: 1.2rem;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .centered-table {
        width: 100%;
        min-width: 500px;
        border-collapse: collapse;
        font-size: 13.5px;
        background-color: #ffffff;
    }
    .centered-table th {
        background-color: #f8fafc;
        color: #475569;
        font-weight: 700;
        text-align: center !important;
        padding: 12px 10px;
        border-bottom: 2px solid #e2e8f0;
        border-right: 1px solid #f1f5f9;
        white-space: nowrap;
    }
    .centered-table td {
        text-align: center !important;
        padding: 11px 8px;
        border-bottom: 1px solid #f1f5f9;
        border-right: 1px solid #f1f5f9;
        color: #1e293b;
        vertical-align: middle;
        word-break: keep-all;
    }
    .centered-table tr:hover {
        background-color: #f1f5f9;
    }
    .centered-table th:last-child, .centered-table td:last-child {
        border-right: none;
    }
    </style>
    <div class="centered-table-container">
    <table class="centered-table">
        <thead>
            <tr>
    """
    for col in df.columns:
        width_style = f" style='width: {col_widths[col]};'" if col_widths and col in col_widths else ""
        html += f"<th{width_style}>{col}</th>"
    html += "</tr></thead><tbody>"
    
    for _, row in df.iterrows():
        html += "<tr>"
        for col in df.columns:
            html += f"<td>{row[col]}</td>"
        html += "</tr>"
        
    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)

# -------------------------------------------------------------
# 자위소방대 명단 불러오기 함수
# -------------------------------------------------------------
def get_roster_data():
    csv_path = os.path.join(BASE_DIR, "roster.csv")
    xlsx_path = os.path.join(BASE_DIR, "roster.xlsx")
    kr_path = os.path.join(BASE_DIR, "자위소방대_명단.xlsx")
    
    try:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
        elif os.path.exists(xlsx_path):
            df = pd.read_excel(xlsx_path, engine='openpyxl')
        elif os.path.exists(kr_path):
            df = pd.read_excel(kr_path, engine='openpyxl')
        else:
            return pd.DataFrame()

        df.columns = [str(c).strip() for c in df.columns]
        if "이름" in df.columns:
            df["이름"] = df["이름"].astype(str).str.strip()
        return df
    except Exception:
        return pd.DataFrame()

# -------------------------------------------------------------
# 소방청 보도자료 수집 함수 (실시간 크롤링)
# -------------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_safety_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    articles = []
    
    try:
        url = "https://www.nfa.go.kr/nfa/news/pressrelease/press/"
        r = requests.get(url, headers=headers, timeout=5, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            items = soup.select("table.board_list tbody tr")
            for item in items:
                a_tag = item.select_one("td.title a") or item.select_one("a")
                if a_tag:
                    title = a_tag.get_text(strip=True)
                    href = a_tag.get("href", "")
                    
                    if href.startswith("/"):
                        link = f"https://www.nfa.go.kr{href}"
                    elif href.startswith("./"):
                        link = f"https://www.nfa.go.kr/nfa/news/pressrelease/press/{href[2:]}"
                    elif not href.startswith("http"):
                        link = f"https://www.nfa.go.kr/nfa/news/pressrelease/press/{href}"
                    else:
                        link = href
                        
                    articles.append({"title": title, "link": link})
                if len(articles) >= 5:
                    break
    except Exception:
        pass

    if not articles:
        articles = [
            {"title": "재난대응 역량 강화를 위한 소방·경찰·해양경찰 간부후보생 합동 교육훈련", "link": "https://www.nfa.go.kr/nfa/news/pressrelease/press/"},
            {"title": "소방청, 필승교 수위 상승에 중앙긴급구조통제단 가동", "link": "https://www.nfa.go.kr/nfa/news/pressrelease/press/"},
            {"title": "소방청, 인천 서해구 쿠팡32물류센터 화재 「중앙화재 합동조사단」 운영", "link": "https://www.nfa.go.kr/nfa/news/pressrelease/press/"},
            {"title": "벌 쏘임 사고 집중 시기… 소방청, 여름철 야외활동 안전수칙 준수 당부", "link": "https://www.nfa.go.kr/nfa/news/pressrelease/press/"},
            {"title": "대한민국 밧줄(로프)구조 세계적 경쟁력 강화…국제 기술교류 합동훈련 개최", "link": "https://www.nfa.go.kr/nfa/news/pressrelease/press/"}
        ]

    return articles

# -------------------------------------------------------------
# 인터넷 뉴스 (네이버/구글 검색 RSS) 실시간 수집 함수
# -------------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_internet_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    articles = []
    query = urllib.parse.quote("소방 OR 화재")
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        r = requests.get(rss_url, headers=headers, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "xml")
            items = soup.find_all("item")
            
            for item in items[:5]:
                title = item.title.text if item.title else ""
                link = item.link.text if item.link else ""
                
                if " - " in title:
                    title_clean = title.rsplit(" - ", 1)[0]
                    media_name = title.rsplit(" - ", 1)[1]
                else:
                    title_clean = title
                    media_name = "인터넷 뉴스"

                articles.append({
                    "title": title_clean,
                    "media": media_name,
                    "link": link
                })
    except Exception:
        pass

    if not articles:
        articles = [
            {"title": "소방청, 여름철 화재 및 안전사고 대비 현장 점검 강화", "media": "소방신문", "link": "#"},
            {"title": "전기차 충전시설 소방안전 기준 강화 방안 추진", "media": "안전일보", "link": "#"},
            {"title": "물류창고 소방시설 특별점검 실시", "media": "이투데이", "link": "#"},
            {"title": "초고층 건축물 화재 예방을 위한 소방훈련 진행", "media": "연합뉴스", "link": "#"},
            {"title": "소방안전관리자 자격 요건 및 정기교육 안내", "media": "경향신문", "link": "#"}
        ]

    return articles

# =============================================================
# [섹션 1] 나의 자위소방대 임무 찾기
# =============================================================
st.subheader("🔍 나의 자위소방대 임무 찾기")
search_name = st.text_input("본인 이름을 입력하고 Enter를 누르세요.", placeholder="예: 홍길동")

df_roster = get_roster_data()

if search_name.strip():
    if not df_roster.empty and "이름" in df_roster.columns:
        clean_search = search_name.strip()
        result = df_roster[df_roster["이름"].str.contains(clean_search, na=False)]
        
        if not result.empty:
            for _, row in result.iterrows():
                with st.container():
                    st.markdown(f"""
                        <div style="background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 12px; padding: 18px; margin-bottom: 12px;">
                            <div style="font-size: 1.1rem; font-weight: 700; color: #1b2a4a; margin-bottom: 10px;">
                                🎯 <b>{row['이름']}</b>님의 자위소방대 정보
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    c1.metric("소속팀", str(row.get("소속팀", "-")))
                    c2.metric("자위소방대 조직", str(row.get("자위소방대 조직", "-")))
                    
                    role_text = str(row.get("개인별 역할", "-"))
                    st.markdown("**📋 개인별 역할:**")
                    st.info(role_text)
        else:
            st.warning(f"'{search_name}' 이름으로 등록된 자위소방대원이 없습니다. 명단을 다시 확인해 주세요.")
    else:
        st.warning("⚠️ 명단 파일이 비어있거나 올바르게 로드되지 않았습니다.")

st.markdown("---")

# =============================================================
# [섹션 2] 비상대응 조직표 (수정 완료: 2번 톤앤톤 적용)
# =============================================================
st.subheader("🏢 비상대응 조직표")

with st.expander("🔻 자위소방대 비상대응 조직도 보기 (클릭하여 펼치기)", expanded=False):
    st.markdown("""
        <style>
        .tree-top {
            border: 2px solid #1b2a4a;
            background: linear-gradient(135deg, #1b2a4a 0%, #0f172a 100%);
            border-radius: 10px;
            padding: 14px;
            text-align: center;
            font-weight: 800;
            font-size: 17px;
            color: #ffffff;
            max-width: 440px;
            margin: 0 auto;
            box-shadow: 0 4px 10px rgba(27, 42, 74, 0.15);
        }
        .v-line {
            width: 2px;
            background-color: #cbd5e1;
            height: 22px;
            margin: 0 auto;
        }
        .h-line {
            border-top: 2px solid #cbd5e1;
            width: 72%;
            margin: 0 auto;
        }
        .dept-card {
            border-radius: 12px;
            padding: 14px;
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            margin-bottom: 12px;
            text-align: center;
            transition: transform 0.2s;
        }
        .dept-card:hover {
            transform: translateY(-3px);
        }
        .dept-head {
            font-weight: 700;
            padding: 8px 10px;
            border-radius: 8px;
            text-align: center;
            color: #ffffff;
            font-size: 14px;
            margin-bottom: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        }
        .sub-box {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 8px 10px;
            margin-top: 8px;
            font-size: 13px;
            text-align: center;
        }
        .sub-title {
            font-weight: 700;
            color: #1e293b;
        }
        .sub-team {
            color: #64748b;
            font-size: 12px;
            display: block;
            margin-top: 3px;
        }
        .night-card {
            border: 1px solid #e2e8f0;
            background-color: #ffffff;
            border-radius: 10px;
            padding: 14px;
            text-align: center;
            box-shadow: 0 2px 6px rgba(0,0,0,0.03);
            height: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="tree-top">대장 : CSO (안전보건총괄책임자)</div>', unsafe_allow_html=True)
    st.markdown('<div class="v-line"></div>', unsafe_allow_html=True)
    st.markdown('<div class="h-line"></div>', unsafe_allow_html=True)
    st.markdown('<div class="v-line"></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
            <div class="dept-card" style="border-top: 4px solid #1b2a4a;">
                <div class="dept-head" style="background-color: #1b2a4a;">
                    소방지휘 본부대장<br><span style="font-size: 12px; font-weight: normal; opacity: 0.9;">(기술본부장)</span>
                </div>
                <div class="sub-box">
                    <span class="sub-title">지휘반</span>
                    <span class="sub-team">안전환경팀</span>
                </div>
                <div class="sub-box">
                    <span class="sub-title">훈련 및 소화반</span>
                    <span class="sub-team">기계팀, 운영팀</span>
                </div>
                <div class="sub-box">
                    <span class="sub-title">피난유도반</span>
                    <span class="sub-team">계전팀</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
            <div class="dept-card" style="border-top: 4px solid #3b5998;">
                <div class="dept-head" style="background-color: #3b5998;">
                    상황 통제본부대장<br><span style="font-size: 12px; font-weight: normal; opacity: 0.9;">(경영기획본부장)</span>
                </div>
                <div class="sub-box">
                    <span class="sub-title">비상연락반</span>
                    <span class="sub-team">조직문화팀</span>
                </div>
                <div class="sub-box">
                    <span class="sub-title">경계반</span>
                    <span class="sub-team">기획재무팀, DX혁신팀</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
            <div class="dept-card" style="border-top: 4px solid #6b7c96;">
                <div class="dept-head" style="background-color: #6b7c96;">
                    의료구호 본부대장<br><span style="font-size: 12px; font-weight: normal; opacity: 0.9;">(사업본부장)</span>
                </div>
                <div class="sub-box">
                    <span class="sub-title">의료반</span>
                    <span class="sub-team">ESG추진팀, 대외협력팀</span>
                </div>
                <div class="sub-box">
                    <span class="sub-title">후송반</span>
                    <span class="sub-team">고객지원팀</span>
                </div>
                <div class="sub-box">
                    <span class="sub-title">방호조치 및 복구반</span>
                    <span class="sub-team">네트워크팀</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # [본부별 통합 줄글 형태] 각 반별 세부 임무
    # -------------------------------------------------------------
    with st.expander("📋 **각 본부 및 반별 세부 임무 상세 보기 (클릭하여 펼치기)**", expanded=False):
        st.markdown("""
            <div class="task-card">
                <div class="task-card-header" style="color: #1b2a4a; border-color: #1b2a4a;">
                    🏛️ 소방지휘본부 (본부대장: 기술본부장)
                </div>
                <div class="task-item">
                    • <b>지휘반 (안전환경팀) :</b> 직장반 차석순으로 부대장의 임무수행보조, 연간 및 월간 소방안전관리계획 수립 및 실시
                </div>
                <div class="task-item">
                    • <b>훈련 및 소화반 (기계팀, 운영팀) :</b> 자체소방시설을 활용한 초기화재 진압활동, 소화용수의 보존과 급수
                </div>
                <div class="task-item">
                    • <b>피난유도반 (계전팀) :</b> 재실자 층별대피유도 및 방화문폐쇄, 재실자 인명검색구조 및 대피경로 안내
                </div>
            </div>

            <div class="task-card">
                <div class="task-card-header" style="color: #3b5998; border-color: #3b5998;">
                    🏢 상황통제본부 (본부대장: 경영기획본부장)
                </div>
                <div class="task-item">
                    • <b>비상연락반 (조직문화팀) :</b> 119신고 및 소내전파, 관계기관에 통보
                </div>
                <div class="task-item">
                    • <b>경계반 (기획재무팀, DX혁신팀) :</b> 중요물품 반출이동, 반출물건의 경비, 출입인원 통제
                </div>
            </div>

            <div class="task-card">
                <div class="task-card-header" style="color: #6b7c96; border-color: #6b7c96;">
                    🏥 의료구호본부 (본부대장: 사업본부장)
                </div>
                <div class="task-item">
                    • <b>의료반 (ESG추진팀, 대외협력팀) :</b> 질식, 화상 등 중경상자의 응급처치
                </div>
                <div class="task-item">
                    • <b>후송반 (고객지원팀) :</b> 사망자 안치 및 지정병원으로의 긴급 후송 지원
                </div>
                <div class="task-item">
                    • <b>방호조치 및 복구반 (네트워크팀) :</b> 관할소방서의 유도, 가스 위험물 등 소방활동상의 장애물 제거 및 복구
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    st.markdown("<h5 style='text-align: center; color: #0f172a; font-weight: 700;'>🌙 야간 및 공휴일 비상대응 조직 (총원: 6명)</h5>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 13px; margin-bottom: 14px;'>※ 교대근무자 5명 + 경비원 1명</p>", unsafe_allow_html=True)

    st.markdown("""
        <div style="border: 2px solid #1b2a4a; background: #1b2a4a; border-radius: 10px; padding: 12px; text-align: center; max-width: 400px; margin: 0 auto; font-weight: 700; color: #ffffff; font-size: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            임시소방대장 : 운영그룹장 (1명)
        </div>
        <div class="v-line"></div>
    """, unsafe_allow_html=True)

    n1, n2, n3 = st.columns(3)
    with n1:
        st.markdown("""
            <div class="night-card" style="border-top: 3px solid #3b5998;">
                <div style="font-weight: 700; color: #3b5998; font-size: 14px; margin-bottom: 4px;">비상연락반</div>
                <div style="color: #475569; font-size: 13px;">CCR근무자 (2명)</div>
            </div>
        """, unsafe_allow_html=True)
    with n2:
        st.markdown("""
            <div class="night-card" style="border-top: 3px solid #3b5998;">
                <div style="font-weight: 700; color: #3b5998; font-size: 14px; margin-bottom: 4px;">소화반</div>
                <div style="color: #475569; font-size: 13px;">현장근무자 (2명)</div>
            </div>
        """, unsafe_allow_html=True)
    with n3:
        st.markdown("""
            <div class="night-card" style="border-top: 3px solid #6b7c96;">
                <div style="font-weight: 700; color: #6b7c96; font-size: 14px; margin-bottom: 4px;">소방대유도반</div>
                <div style="color: #475569; font-size: 13px;">경비원 (1명)</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================
# [섹션 3] 비상 대피소 안내
# =============================================================
st.subheader("🚨 비상 대피소 안내")

c_shelter1, c_shelter2 = st.columns(2)

with c_shelter1:
    with st.expander("🚩 **1차대피소 위치 및 피난동선 확인**", expanded=False):
        st.error("🚩 **1차 대피소 : 관리동 뒤 쪽문**")
        st.markdown("* 건물에서 빠져나와 즉시 집결하여 팀별 인원 파악을 실시하는 장소입니다.")
        
        img1_path = os.path.join(BASE_DIR, "shelter1_1.jpg") if os.path.exists(os.path.join(BASE_DIR, "shelter1_1.jpg")) else os.path.join(BASE_DIR, "shelter1_1.jpg.jpg")
        img2_path = os.path.join(BASE_DIR, "shelter1_2.jpg") if os.path.exists(os.path.join(BASE_DIR, "shelter1_2.jpg")) else os.path.join(BASE_DIR, "shelter1_2.jpg.jpg")
        
        if os.path.exists(img1_path): st.image(img1_path, caption="1차 대피소 현장 위치 및 전경", use_container_width=True)
        if os.path.exists(img2_path): st.image(img2_path, caption="1차 대피소 비상 피난 동선 도면", use_container_width=True)

with c_shelter2:
    with st.expander("⚠️ **2차대피소 위치 및 피난동선 확인**", expanded=False):
        st.warning("⚠️ **2차 대피소: 셀트리온 정문**")
        st.markdown("* 화재 및 누출 규모가 커 대내외 확산 우려가 있을 경우 이동하는 장소입니다.")
        
        img3_path = os.path.join(BASE_DIR, "shelter2.jpg") if os.path.exists(os.path.join(BASE_DIR, "shelter2.jpg")) else os.path.join(BASE_DIR, "shelter2.jpg.jpg")
        if os.path.exists(img3_path): st.image(img3_path, caption="2차 대피소(셀트리온 정문) 및 피해 예상 반경", use_container_width=True)

st.markdown("---")

# =============================================================
# [섹션 4] 사고대응 유관기관 비상연락체계
# =============================================================
st.subheader("📞 사고대응 유관기관 비상연락체계")

contact_data = [
    {"구분": "정부", "명칭(담당자)": "중부지방고용노동청", "전화번호": "032-460-6248", "비고": "고용노동부"},
    {"구분": "정부", "명칭(담당자)": "중대산업사고예방센터", "전화번호": "031-364-7508", "비고": "고용노동부"},
    {"구분": "정부", "명칭(담당자)": "시흥화학재난합동방재센터", "전화번호": "031-470-2454", "비고": "-"},
    {"구분": "유관기관", "명칭(담당자)": "한국에너지공단 분산에너지처", "전화번호": "010-5589-3342", "비고": "-"},
    {"구분": "유관기관", "명칭(담당자)": "산업안전보건공단 인천광역본부", "전화번호": "032-510-0500", "비고": "-"},
    {"구분": "유관기관", "명칭(담당자)": "인천광역시 안전상황실", "전화번호": "032-440-1881", "비고": "-"},
    {"구분": "유관기관", "명칭(담당자)": "연수구청 재난안전본부", "전화번호": "080-040-3650", "비고": "-"},
    {"구분": "유관기관", "명칭(담당자)": "송도 119안전센터", "전화번호": "032-810-6683", "비고": "-"},
    {"구분": "유관기관", "명칭(담당자)": "경찰민원 콜센터", "전화번호": "182", "비고": "-"},
    {"구분": "유관기관", "명칭(담당자)": "송도국제도시 지구대", "전화번호": "032-822-1112", "비고": "-"},
    {"구분": "유관기관", "명칭(담당자)": "한국가스공사 인천지역본부", "전화번호": "주간: 032-453-6637 / 야간: 032-453-6555", "비고": "-"},
    {"구분": "유관기관", "명칭(담당자)": "한국가스안전공사 인천본부", "전화번호": "032-435-1525", "비고": "-"},
    {"구분": "유관기관", "명칭(담당자)": "한국전기안전공사 인천본부", "전화번호": "032-290-7000", "비고": "-"},
    {"구분": "유관기관", "명칭(담당자)": "한국전력 송도변전소", "전화번호": "031-363-5356", "비고": "-"},
    {"구분": "유관기관", "명칭(담당자)": "삼천리 종합상황실", "전화번호": "080-3002-118", "비고": "-"},
    {"구분": "인근사업장", "명칭(담당자)": "셀트리온", "전화번호": "032-850-5119", "비고": "-"},
    {"구분": "인근사업장", "명칭(담당자)": "공영차고지", "전화번호": "032-814-0900", "비고": "-"},
    {"구분": "인근사업장", "명칭(담당자)": "송도하수처리장", "전화번호": "032-899-4658", "비고": "-"},
    {"구분": "인근사업장", "명칭(담당자)": "KD Corporation", "전화번호": "031-499-0815", "비고": "-"},
    {"구분": "협력업체", "명칭(담당자)": "이우현 소장", "전화번호": "010-2310-9417", "비고": "소장"},
    {"구분": "협력업체", "명칭(담당자)": "신재을 팀장", "전화번호": "010-6220-0913", "비고": "기계 관리감독자"},
    {"구분": "협력업체", "명칭(담당자)": "신명규 팀장", "전화번호": "010-8501-4325", "비고": "전기 관리감독자"},
    {"구분": "협력업체", "명칭(담당자)": "김요한 팀장", "전화번호": "010-4109-5114", "비고": "계전 관리감독자"},
]

df_contacts = pd.DataFrame(contact_data)
selected_category = st.selectbox("📂 구분별 필터 선택", ["전체 보기", "정부", "유관기관", "인근사업장", "협력업체"])

if selected_category != "전체 보기":
    filtered_df = df_contacts[df_contacts["구분"] == selected_category]
else:
    filtered_df = df_contacts

render_centered_table(filtered_df, col_widths={"구분": "15%", "명칭(담당자)": "35%", "전화번호": "30%", "비고": "20%"})

st.markdown("---")

# =============================================================
# [섹션 5] 주요 소방시설 위치
# =============================================================
st.subheader("💧 주요 소방시설 (수신반 & 상수도) 위치")

col_rec, col_water = st.columns(2)

st.markdown("""
    <style>
    .facility-box {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        background-color: #ffffff;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        height: 100%;
        transition: transform 0.2s ease;
    }
    .facility-box:hover {
        transform: translateY(-2px);
    }
    .facility-title-navy {
        color: #1b2a4a;
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .facility-title-blue {
        color: #3b5998;
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .facility-content {
        font-size: 0.93rem;
        line-height: 1.65;
        color: #334155;
    }
    .facility-role-section {
        margin-top: 14px;
    }
    .facility-content ul {
        padding-left: 18px;
        margin: 6px 0 0 0;
    }
    </style>
""", unsafe_allow_html=True)

with col_rec:
    st.markdown("""
    <div class="facility-box">
        <div class="facility-title-navy">🟦 소방 수신반 (수신기) 위치</div>
        <div class="facility-content">
            <div>• <b>설치 장소:</b> <span style="background-color: #f1f5f9; color: #1b2a4a; padding: 2px 6px; border-radius: 4px; font-weight: 700;">주제어동 3층 CCR</span></div>
            <div class="facility-role-section">• <b>주요 역할:</b>
                <ul>
                    <li>사업장 내 화재 감지기/발신기 작동 구역 즉시 확인</li>
                    <li>소내 비상방송 연동 및 주경종/지구경종 상태 수시 제어</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_water:
    st.markdown("""
    <div class="facility-box">
        <div class="facility-title-blue">🟦 상수도 (소화용수) 위치</div>
        <div class="facility-content">
            <div>• <b>설치 장소:</b> <span style="background-color: #f1f5f9; color: #3b5998; padding: 2px 6px; border-radius: 4px; font-weight: 700;">스팀터빈동 주출입구 앞</span></div>
            <div class="facility-role-section">• <b>주요 역할:</b>
                <ul>
                    <li>화재 발생 시 소방차 급수 지원 및 소화용수 보충</li>
                    <li>초기 및 대형 화재 대응 시 주 용수 공급원 역할</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

with st.expander("📍 **소방 수신반 및 상수도 위치 도면 보기 (클릭하여 펼치기)**", expanded=False):
    fp_img_path = None
    fp_candidates = [
        "firepump.jpg", "firepump.png", "firepump.jpeg",
        "FIREPUMP.JPG", "FIREPUMP.PNG", "FIREPUMP.JPEG",
        "Firepump.jpg", "Firepump.png",
        "firepump.jpg.jpg", "FIREPUMP.JPG.JPG"
    ]
    
    for fp_fname in fp_candidates:
        t_path = os.path.join(BASE_DIR, fp_fname)
        if os.path.exists(t_path):
            fp_img_path = t_path
            break
            
    if fp_img_path:
        img_col1, img_col2, img_col3 = st.columns([1, 4, 1])
        with img_col2:
            st.image(fp_img_path, caption="사업장 내 수신반(주제어동 3층 CCR) 및 상수도(스팀터빈동 주출입구 앞) 배치 도면", use_container_width=True)
    else:
        st.warning("⚠️ 소방시설 도면 이미지(firepump.jpg)를 찾을 수 없습니다. GitHub 저장소 상의 정확한 파일명과 대소문자를 확인해 주세요.")

st.markdown("---")
