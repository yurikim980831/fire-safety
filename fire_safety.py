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
# [반응형 CSS] PC 스타일 유지 + 모바일 전용 가독성 및 메인 타이틀 대폭 강조
# =============================================================
st.markdown("""
    <style>
    /* 기본 공통 및 PC 스타일 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    img {
        max-width: 100% !important;
        height: auto !important;
    }
    
    /* 모바일 전용 반응형 스타일 (화면 너비 768px 이하) */
    @media (max-width: 768px) {
        /* 전체 여백 조절 */
        .main .block-container {
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-top: 1rem !important;
        }
        
        /* 🚨 메인 타이틀(st.title) 모바일 폰트 크기 강력 확대 */
        div[data-testid="stTitle"] h1,
        .stTitle > div > h1,
        h1 { 
            font-size: 3.2rem !important; 
            font-weight: 900 !important; 
            line-height: 1.25 !important;
            word-break: keep-all !important;
            color: #0f172a !important;
            margin-bottom: 0.5rem !important;
        }

        /* 서브 타이틀 및 본문 글자 크기 정돈 */
        h2, .stSubheader, [data-testid="stSubheader"] h2 { font-size: 1.4rem !important; font-weight: 700 !important; }
        h3 { font-size: 1.2rem !important; }
        p, div, span { font-size: 0.95rem !important; }

        /* 타임라인 모바일 세로/줄바꿈 배치 */
        .timeline-container {
            flex-direction: column !important;
            gap: 10px !important;
        }
        .timeline-line {
            display: none !important; /* 모바일에서는 중앙선 숨김 */
        }
        .timeline-box {
            width: 100% !important;
            margin-bottom: 6px !important;
            padding: 12px !important;
        }

        /* 카드 및 상자 모바일 여백 정돈 */
        .facility-box, .first-aid-box, .dept-card, .night-card {
            padding: 12px !important;
            margin-bottom: 10px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# 상단 제목
st.title("🚒 사내 소방안전관리 정보 Dashboard")
st.caption(f"안전환경팀 | 최종 업데이트: {datetime.now().strftime('%Y-%m-%d')}")
st.markdown("---")

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
        margin-bottom: 1rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    .centered-table {
        width: 100%;
        min-width: 500px; /* 모바일에서 표 깨짐 방지 */
        border-collapse: collapse;
        font-size: 13px;
        background-color: #ffffff;
    }
    .centered-table th {
        background-color: #f8fafc;
        color: #334155;
        font-weight: bold;
        text-align: center !important;
        padding: 8px 8px;
        border-bottom: 2px solid #e2e8f0;
        border-right: 1px solid #f1f5f9;
        white-space: nowrap;
    }
    .centered-table td {
        text-align: center !important;
        padding: 8px 6px;
        border-bottom: 1px solid #f1f5f9;
        border-right: 1px solid #f1f5f9;
        color: #1e293b;
        vertical-align: middle;
        word-break: keep-all;
    }
    .centered-table tr:hover {
        background-color: #f8fafc;
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
                with st.container(border=True):
                    st.success(f"🎯 **{row['이름']}**님의 자위소방대 정보입니다.")
                    c1, c2 = st.columns(2)
                    c1.metric("소속팀", str(row.get("소속팀", "-")))
                    c2.metric("자위소방대 조직", str(row.get("자위소방대 조직", "-")))
                    
                    role_text = str(row.get("개인별 역할", "-"))
                    st.markdown(f"**📋 개인별 역할:**")
                    st.info(role_text)
        else:
            st.warning(f"'{search_name}' 이름으로 등록된 자위소방대원이 없습니다. 명단을 다시 확인해 주세요.")
    else:
        st.warning("⚠️ 명단 파일이 비어있거나 올바르게 로드되지 않았습니다.")

st.markdown("---")

# =============================================================
# [섹션 2] 비상대응 조직표
# =============================================================
st.subheader("🏢 비상대응 조직표")

with st.expander("🔻 자위소방대 비상대응 조직도 보기 (클릭하여 펼치기)", expanded=False):
    st.markdown("""
        <style>
        .tree-top {
            border: 2px solid #1e293b;
            background-color: #f8fafc;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            font-weight: bold;
            font-size: 16px;
            color: #0f172a;
            max-width: 420px;
            margin: 0 auto;
        }
        .v-line {
            width: 2px;
            background-color: #cbd5e1;
            height: 20px;
            margin: 0 auto;
        }
        .h-line {
            border-top: 2px solid #cbd5e1;
            width: 70%;
            margin: 0 auto;
        }
        .dept-card {
            border-radius: 8px;
            padding: 10px;
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            margin-bottom: 12px;
            text-align: center;
        }
        .dept-head {
            font-weight: bold;
            padding: 6px;
            border-radius: 4px;
            text-align: center;
            color: #ffffff;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .sub-box {
            background-color: #f8fafc;
            border: 1px dashed #cbd5e1;
            border-radius: 6px;
            padding: 6px 8px;
            margin-top: 6px;
            font-size: 13px;
            text-align: center;
        }
        .sub-title {
            font-weight: bold;
            color: #334155;
        }
        .sub-team {
            color: #64748b;
            font-size: 12px;
            display: block;
            margin-top: 2px;
        }
        .night-card {
            border: 1px solid #cbd5e1;
            background-color: #ffffff;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
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
            <div class="dept-card" style="border-top: 3px solid #ef4444;">
                <div class="dept-head" style="background-color: #ef4444;">
                    소방지휘 본부대장<br><span style="font-size: 12px; font-weight: normal;">(기술본부장)</span>
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
                    <span class="sub-team">계전팀, 네트워크팀</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
            <div class="dept-card" style="border-top: 3px solid #3b82f6;">
                <div class="dept-head" style="background-color: #3b82f6;">
                    상황 통제본부대장<br><span style="font-size: 12px; font-weight: normal;">(경영기획본부장)</span>
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
            <div class="dept-card" style="border-top: 3px solid #10b981;">
                <div class="dept-head" style="background-color: #10b981;">
                    의료구호 본부대장<br><span style="font-size: 12px; font-weight: normal;">(사업본부장)</span>
                </div>
                <div class="sub-box">
                    <span class="sub-title">의료반</span>
                    <span class="sub-team">ESG추진팀</span>
                </div>
                <div class="sub-box">
                    <span class="sub-title">후송반</span>
                    <span class="sub-team">대외협력팀</span>
                </div>
                <div class="sub-box">
                    <span class="sub-title">방호 및 복구반</span>
                    <span class="sub-team">고객지원팀</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    st.markdown("<h5 style='text-align: center; color: #1e293b;'>🌙 야간 및 공휴일 비상대응 조직 (총원: 6명)</h5>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 13px; margin-bottom: 12px;'>※ 교대근무자 5명 + 경비원 1명</p>", unsafe_allow_html=True)

    st.markdown("""
        <div style="border: 2px solid #64748b; background-color: #f8fafc; border-radius: 8px; padding: 10px; text-align: center; max-width: 400px; margin: 0 auto; font-weight: bold; color: #0f172a; font-size: 15px;">
            임시소방대장 : 운영그룹장 (1명)
        </div>
        <div class="v-line"></div>
    """, unsafe_allow_html=True)

    n1, n2, n3 = st.columns(3)
    with n1:
        st.markdown("""
            <div class="night-card" style="border-top: 3px solid #3b82f6;">
                <div style="font-weight: bold; color: #1d4ed8; font-size: 14px; margin-bottom: 4px;">비상연락반</div>
                <div style="color: #475569; font-size: 13px;">CCR근무자 (2명)</div>
            </div>
        """, unsafe_allow_html=True)
    with n2:
        st.markdown("""
            <div class="night-card" style="border-top: 3px solid #f59e0b;">
                <div style="font-weight: bold; color: #b45309; font-size: 14px; margin-bottom: 4px;">소화반</div>
                <div style="color: #475569; font-size: 13px;">현장근무자 (2명)</div>
            </div>
        """, unsafe_allow_html=True)
    with n3:
        st.markdown("""
            <div class="night-card" style="border-top: 3px solid #10b981;">
                <div style="font-weight: bold; color: #047857; font-size: 14px; margin-bottom: 4px;">소방대유도반</div>
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
        border-radius: 8px;
        padding: 16px;
        background-color: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        height: 100%;
    }
    .facility-title-red {
        color: #dc2626;
        font-weight: bold;
        font-size: 16px;
        margin-bottom: 12px;
    }
    .facility-title-blue {
        color: #2563eb;
        font-weight: bold;
        font-size: 16px;
        margin-bottom: 12px;
    }
    .facility-content {
        font-size: 13.5px;
        line-height: 1.6;
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
        <div class="facility-title-red">🟥 소방 수신반 (수신기) 위치</div>
        <div class="facility-content">
            <div>• <b>설치 장소:</b> <b>주제어동 3층 CCR</b></div>
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
            <div>• <b>설치 장소:</b> <b>스팀터빈동 주출입구 앞</b></div>
            <div class="facility-role-section">• <b>주요 역할:</b>
                <ul>
                    <li>화재 발생 시 소방차 급수 지원 및 소화용수 보충</li>
                    <li>초기 및 대형 화재 대응 시 주 용수 공급원 역할</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

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
        # 반응형 너비로 설정하여 모바일 및 PC 화면에 맞춤
        img_col1, img_col2, img_col3 = st.columns([1, 4, 1])
        with img_col2:
            st.image(fp_img_path, caption="사업장 내 수신반(주제어동 3층 CCR) 및 상수도(스팀터빈동 주출입구 앞) 배치 도면", use_container_width=True)
    else:
        st.warning("⚠️ 소방시설 도면 이미지(firepump.jpg)를 찾을 수 없습니다. GitHub 저장소 상의 정확한 파일명과 대소문자를 확인해 주세요.")

st.markdown("---")

# =============================================================
# [섹션 6] 응급처치 가이드 (CPR 및 AED)
# =============================================================
st.subheader("💚 응급처치 가이드 (CPR 및 AED 사용법)")

st.markdown("""
    <style>
    .first-aid-box {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        background-color: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    </style>
""", unsafe_allow_html=True)

cpr_col, aed_col = st.columns(2)

with cpr_col:
    st.markdown("""
    <div class="first-aid-box">
        <h5 style="font-weight: bold; margin-bottom: 12px; color: #1e293b; font-size: 16px;">🫀 심폐소생술(CPR) 방법</h5>
        <div style="font-size: 13.5px; line-height: 1.6; color: #1e293b; flex-grow: 1;">
        <ol style="padding-left: 18px; margin: 0;">
            <li style="margin-bottom: 8px;"><b>의식 및 호흡 확인:</b> 어깨를 가볍게 두드리며 반응 및 정상 호흡 여부를 확인합니다.</li>
            <li style="margin-bottom: 8px;"><b>119 신고 및 AED 요청:</b> 주변 사람을 특정하여 119 신고와 AED를 가져오도록 지시합니다.</li>
            <li style="margin-bottom: 8px;"><b>가슴압박 30회 실시:</b>
                <ul style="padding-left: 16px; margin-top: 2px;">
                    <li>깍지 낀 두 손으로 가슴 중앙(양 젖꼭지 연결선 한가운데)을 누릅니다.</li>
                    <li><b>압박 깊이:</b> 약 5cm / <b>속도:</b> 분당 100~120회</li>
                </ul>
            </li>
            <li style="margin-bottom: 8px;"><b>인공호흡 2회 실시:</b> 기도를 확보한 후 환자의 코를 막고 가슴이 부풀어 오르도록 2회 숨을 넣습니다.</li>
            <li><b>무한 반복:</b> 119 구급대 도착 시까지 <b>가슴압박 30회 + 인공호흡 2회</b>를 반복합니다.</li>
        </ol>
        </div>
    </div>
    """, unsafe_allow_html=True)

with aed_col:
    st.markdown("""
    <div class="first-aid-box">
        <h5 style="font-weight: bold; margin-bottom: 12px; color: #1e293b; font-size: 16px;">⚡ 자동심장충격기(AED) 사용법</h5>
        <div style="font-size: 13.5px; line-height: 1.6; color: #1e293b; flex-grow: 1;">
        <ol style="padding-left: 18px; margin: 0;">
            <li style="margin-bottom: 8px;"><b>전원 켜기:</b> AED를 환자 옆에 두고 전원 버튼을 누릅니다. (음성 지시 시작)</li>
            <li style="margin-bottom: 8px;"><b>패드 부착:</b> 
                <ul style="padding-left: 16px; margin-top: 2px;">
                    <li><b>패드 1:</b> 오른쪽 빗장뼈(쇄골) 아래</li>
                    <li><b>패드 2:</b> 왼쪽 젖꼭지 아래 겨드랑이선</li>
                </ul>
            </li>
            <li style="margin-bottom: 8px;"><b>심장리듬 분석:</b> "분석 중..." 음성이 나오면 <b>환자에게서 물러납니다.</b></li>
            <li style="margin-bottom: 8px;"><b>제세동(전기충격):</b> 충전 후 버튼이 깜빡이면 <b>모두 물러선 것을 확인 후 눌러줍니다.</b></li>
            <li><b>즉시 CPR 재개:</b> 전기충격 직후 즉시 가슴압박을 다시 시작합니다.</li>
        </ol>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

with st.expander("📍 **사내 AED(자동심장충격기) 설치 위치 및 안내문 보기 (클릭하여 펼치기)**", expanded=False):
    aed_img_path = None
    for aed_fname in ["AED.jpg", "aed.jpg", "AED.PNG", "aed.png"]:
        t_path = os.path.join(BASE_DIR, aed_fname)
        if os.path.exists(t_path):
            aed_img_path = t_path
            break
            
    if aed_img_path:
        # 반응형 너비로 설정하여 모바일 및 PC 화면에 맞춤
        aed_col1, aed_col2, aed_col3 = st.columns([1, 4, 1])
        with aed_col2:
            st.image(aed_img_path, caption="사내 AED 설치 장소 (관리동 3층 E/V 앞, 주제어동 CCR 앞) 및 주의사항", use_container_width=True)
    else:
        st.warning("⚠️ AED 비치 위치 이미지(AED.jpg)가 폴더에 없습니다. 이미지 파일명을 확인해 주세요.")

st.markdown("---")

# =============================================================
# [섹션 7] 25년 소방훈련 세부 시나리오
# =============================================================
st.subheader("📋 25년 소방훈련 세부 시나리오")
st.caption("🚨 **상황:** 정문 주차장 급속충전 중인 전기차량('코나') 화재 발생")

tab1, tab2, tab3, tab4 = st.tabs([
    "1단계: 화재발생 & 신고", 
    "2단계: 초기소화 & 대피", 
    "3단계: 소방차 유도 & 강평",
    "🖼️ 참고: 이미지로 확인하기"
])

scenario_widths = {"시간": "15%", "담당자": "20%", "조치내용": "45%", "비고": "20%"}

with tab1:
    st.markdown("##### 📢 상황 인지 및 소내 전파 (14:00 ~ 14:04)")
    scenario_data_1 = [
        {"시간": "14:00~14:02", "담당자": "로컬근무자 ➡ CCR", "조치내용": "급속충전 중인 전기차 화재 목격 및 CCR 상황전파 (\"불이야! 불이야!\")", "비고": "연막탄 6EA 세팅, 사이렌 송출"},
        {"시간": "14:02", "담당자": "운영리더", "조치내용": "화재발생 상황 소내 전파 및 CO에게 소방서 신고 지시", "비고": "-"},
        {"시간": "14:02", "담당자": "운전원 (CO)", "조치내용": "119 소방서 화재 신고 (인천종합에너지 정문 주차장 전기차 화재)", "비고": "-"},
        {"시간": "14:04", "담당자": "비상연락반 (경영지원팀)", "조치내용": "페이지폰 소내 대피 방송 실시 (2회)", "비고": "-"},
    ]
    render_centered_table(pd.DataFrame(scenario_data_1), scenario_widths)

with tab2:
    st.markdown("##### 🧯 초기소화 및 전직원 대피 (14:02 ~ 14:10)")
    scenario_data_2 = [
        {"시간": "14:02~14:05", "담당자": "훈련 및 소화반 (운영/기계)", "조치내용": "옥외소화전함 개방, 호스 전개/연결 및 방수 위치 확보 후 방수 실시", "비고": "약 1분간 방사"},
        {"시간": "14:05", "담당자": "피난유도반 (계전팀)", "조치내용": "각 층 비상계단 대피 유도 및 잔류자 확인 후 최종 퇴실", "비고": "층별 담당자 지정"},
        {"시간": "14:05~14:10", "담당자": "전직원", "조치내용": "1차 대피소(1층 정문)로 신속 대피, 팀별 인원 체크 후 소방안전관리자 보고", "비고": "대피 완료 후 시연 관람"},
        {"시간": "14:05~14:10", "담당자": "소화반", "조치내용": "충전기 옆 질식포 보관함에서 질식포 수령 후 화재차량 질식소화 전개", "비고": "화염 추가확산 방지"},
    ]
    render_centered_table(pd.DataFrame(scenario_data_2), scenario_widths)

with tab3:
    st.markdown("##### 🚒 모의소방차 진입 및 훈련 종료 (14:10 ~ 14:15)")
    scenario_data_3 = [
        {"시간": "14:10~14:11", "담당자": "방호 및 복구반 (네트워크팀)", "조치내용": "모의소방차 진입 요청 및 정문/주차장 진입 유도 (유도자 2인 배치)", "비고": "진입 완료 시 상황 종료"},
        {"시간": "14:11~14:15", "담당자": "소방안전관리자 (김유리)", "조치내용": "안전보건총괄책임자에게 대피인원 및 피해상황 보고", "비고": "-"},
        {"시간": "14:11~14:15", "담당자": "자위소방대장 / 119안전센터", "조치내용": "훈련 실시 완료 보고 및 신송119안전센터 최종 훈련 강평", "비고": "피드백 차후 적용"},
    ]
    render_centered_table(pd.DataFrame(scenario_data_3), scenario_widths)

with tab4:
    st.markdown("##### 📄 원본 세부 시나리오 문서 이미지")
    images_info = [
        (["fire drill_1.jpg", "fire_drill_1.jpg"], "1페이지: 화재발생 인지 및 신고 / 소내 전파"),
        (["fire drill_2.jpg", "fire_drill_2.jpg"], "2페이지: 대피방송, 피난유도 & 현장위치(소화전, 모의차량)"),
        (["fire drill_3.jpg", "fire_drill_3.jpg"], "3페이지: 비상대피 현장 & 질식소화포 보관함 위치"),
        (["fire drill_4.jpg", "fire_drill_4.jpg"], "4페이지: 모의 소방차 대기장소 및 유도자 위치"),
        (["fire drill_5.jpg", "fire_drill_5.jpg"], "5페이지: 훈련 종료 및 강평 문서")
    ]
    for file_candidates, caption in images_info:
        found_path = None
        for fname in file_candidates:
            path = os.path.join(BASE_DIR, fname)
            if os.path.exists(path):
                found_path = path
                break
        if found_path:
            # 반응형 너비로 설정하여 모바일 및 PC 화면에 맞춤
            s_col1, s_col2, s_col3 = st.columns([1, 4, 1])
            with s_col2:
                st.image(found_path, caption=caption, use_container_width=True)
            st.markdown("---")

st.markdown("---")

# =============================================================
# [섹션 8] 연간 소방안전관리 일정
# =============================================================
st.subheader("📅 연간 소방안전관리 일정")

st.markdown("""
    <style>
    .timeline-wrapper {
        position: relative;
        padding: 10px 0;
        margin: 20px 0 10px 0;
    }
    .timeline-line {
        position: absolute;
        top: 50%;
        left: 4%;
        right: 4%;
        height: 3px;
        background-color: #dbebe6;
        z-index: 1;
        transform: translateY(-50%);
    }
    .timeline-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: relative;
        z-index: 2;
    }
    .timeline-box {
        background: #ffffff;
        border: 2px solid #dbe2ea;
        border-radius: 12px;
        padding: 18px 10px;
        width: 18.5%;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .timeline-box.highlight {
        border-color: #c93b3b;
        background-color: #fdf5f5;
    }
    .timeline-title {
        font-size: 16px;
        font-weight: 800;
        color: #1a202c;
        margin-bottom: 6px;
    }
    .timeline-box.highlight .timeline-title {
        color: #c93b3b;
    }
    .timeline-subtitle {
        font-size: 13.5px;
        font-weight: bold;
        color: #4a5568;
        margin-bottom: 12px;
    }
    .timeline-box.highlight .timeline-subtitle {
        color: #c93b3b;
    }
    .timeline-badge {
        display: inline-block;
        font-size: 11.5px;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 6px;
        background-color: #e8f0fe;
        color: #3b82f6;
    }
    .timeline-box.highlight .timeline-badge {
        background-color: #fce8e8;
        color: #d93838;
    }
    </style>

    <div class="timeline-wrapper">
        <div class="timeline-line"></div>
        <div class="timeline-container">
            <div class="timeline-box">
                <div class="timeline-title">1월~4월</div>
                <div class="timeline-subtitle">상시점검</div>
                <div class="timeline-badge">소방시설 유지</div>
            </div>
            <div class="timeline-box highlight">
                <div class="timeline-title">5월</div>
                <div class="timeline-subtitle">작동점검</div>
                <div class="timeline-badge">소방시설 작동점검</div>
            </div>
            <div class="timeline-box">
                <div class="timeline-title">6월~10월</div>
                <div class="timeline-subtitle">상시점검</div>
                <div class="timeline-badge">일상 안전관리</div>
            </div>
            <div class="timeline-box highlight">
                <div class="timeline-title">11월</div>
                <div class="timeline-subtitle">종합점검 및 자체훈련</div>
                <div class="timeline-badge">종합점검 / 자체훈련</div>
            </div>
            <div class="timeline-box">
                <div class="timeline-title">12월</div>
                <div class="timeline-subtitle">결과보고 및 동절기 화재안전점검</div>
                <div class="timeline-badge">연간 실적 정리</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# 하단 안내 멘트
st.caption("※ 금년도 화재예방안전진단 수검으로 인한 교육·훈련 면제로 12월 합동 교육·훈련이 아닌 자체 실시를 통해 약소화 진행 예정")

st.markdown("---")

# =============================================================
# [섹션 9] 소방 소식 및 실시간 인터넷 뉴스
# =============================================================
st.subheader("📰 소방안전 소식 & 실시간 주요 뉴스")
st.caption("※ 대시보드 접속 시 최신 정보로 자동 갱신됩니다. (10분 주기 자동 캐싱)")

st.markdown("""
    <style>
    .news-card {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 8px;
        background-color: #ffffff;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        height: 82px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .news-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
    }
    .news-title {
        font-size: 13.5px;
        font-weight: bold;
        color: #1e293b;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .news-media {
        font-size: 11px;
        background-color: #f1f5f9;
        color: #475569;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 600;
        white-space: nowrap;
    }
    .news-link {
        font-size: 12px;
        color: #2563eb;
        text-decoration: none;
    }
    .news-link:hover {
        text-decoration: underline;
    }
    </style>
""", unsafe_allow_html=True)

col_official, col_portal = st.columns(2)

# [좌측] 소방청 공식 보도자료
with col_official:
    st.markdown("##### 🏛️ 소방청 공식 보도자료")
    official_releases = fetch_safety_news()
    for rel in official_releases:
        st.markdown(f"""
            <div class="news-card">
                <div class="news-title" title="{rel['title']}">📌 {rel['title']}</div>
                <a class="news-link" href="{rel['link']}" target="_blank">🔗 소방청 원문 보기</a>
            </div>
        """, unsafe_allow_html=True)

# [우측] 인터넷 뉴스 (소방/화재)
with col_portal:
    st.markdown("##### 🔥 실시간 소방·화재 인터넷 뉴스")
    internet_news = fetch_internet_news()
    for news in internet_news:
        st.markdown(f"""
            <div class="news-card">
                <div class="news-header">
                    <span class="news-title" title="{news['title']}">🔥 {news['title']}</span>
                    <span class="news-media">{news['media']}</span>
                </div>
                <a class="news-link" href="{news['link']}" target="_blank">🔗 기사 원문 보기</a>
            </div>
        """, unsafe_allow_html=True)
