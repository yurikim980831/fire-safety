# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib3
import os
from datetime import datetime

# SSL 경고 숨기기 (공공기관 사이트 접속용)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. 페이지 설정
st.set_page_config(page_title="사내 소방안전관리 대시보드", layout="wide", page_icon="🚒")

st.title("🚒 사내 소방안전관리 대시보드")
st.markdown("---")

# 이미지 절대 경로 설정 (OneDrive 폴더 직접 지정)
BASE_DIR = r"C:\Users\김유리\OneDrive - GS에너지\김유리\6. 소방\13. 안전대상\대쉬보드"

# ------------------------------------------------------------------
# [임시 데이터] 자위소방대 명단
# ------------------------------------------------------------------
@st.cache_data
def get_roster_data():
    data = [
        {"이름": "홍길동", "소속본부": "경영지원팀", "자위소방대_반": "지휘통제반", "임무": "대원 소집, 상황 총괄 보고 및 유관기관(소방서) 연락"},
        {"이름": "김철수", "소속본부": "생산1팀", "자위소방대_반": "초기소화반", "임무": "화재 발생 초기 소화기 및 옥내소화전 이용 화재 진압"},
        {"이름": "이영희", "소속본부": "인사팀", "자위소방대_반": "피난유도반", "임무": "대피 통로 확보 및 직원들을 1, 2차 대피소로 신속하게 유도"},
        {"이름": "박민수", "소속본부": "연구소", "자위소방대_반": "구조구급반", "임무": "부상자 발생 시 응급처치 및 안전지대로 이송, 119 구급대 인계"},
    ]
    return pd.DataFrame(data)

# ------------------------------------------------------------------
# [기능] 소방청 보도자료 크롤링 (최신 5건)
# ------------------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_nfa_press_releases():
    url = "https://www.nfa.go.kr/nfa/news/pressrelease/press/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "lxml")
        articles = []
        rows = soup.select("table.board_list tbody tr") or soup.select("table tr")
        
        for row in rows:
            title_link = row.select_one("td.title a") or row.select_one("td a")
            date_cell = row.select_one("td.date") or row.select_all("td")[-1] if row.select("td") else None
            
            if title_link:
                title = title_link.get_text(strip=True)
                href = title_link.get("href", "")
                link = f"https://www.nfa.go.kr{href}" if not href.startswith("http") else href
                date_str = date_cell.get_text(strip=True) if hasattr(date_cell, 'get_text') else "-"
                
                if title and "테스트" not in title:
                    articles.append({"title": title, "link": link, "date": date_str})
                    if len(articles) >= 5:
                        break
        return articles
    except Exception:
        return []

# ------------------------------------------------------------------
# 레이아웃 구성
# ------------------------------------------------------------------
col_left, col_right = st.columns([3, 2])

# ==========================================
# 왼쪽 컬럼 (조회 및 시나리오, 소화기 사용법)
# ==========================================
with col_left:
    st.subheader("🔍 나의 자위소방대 임무 찾기")
    search_name = st.text_input("본인 이름을 입력하고 Enter를 누르세요.", placeholder="예: 홍길동")
    
    if search_name.strip():
        df_roster = get_roster_data()
        result = df_roster[df_roster["이름"].str.contains(search_name, na=False)]
        
        if not result.empty:
            for _, row in result.iterrows():
                with st.container(border=True):
                    st.success(f"🎯 **{row['이름']}**님의 자위소방대 정보입니다.")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("소속본부", row["소속본부"])
                    c2.metric("자위소방대 역할", row["자위소방대_반"])
                    st.markdown(f"**📋 담당 임무:**\n> {row['임무']}")
        else:
            st.warning(f"'{search_name}' 이름으로 등록된 자위소방대원이 없습니다. 명단을 확인해 주세요.")
            
    st.markdown("---")
    
    st.subheader("📋 2025년도 소방훈련 시나리오")
    tab1, tab2, tab3 = st.tabs(["1단계: 화재 발생 및 전파", "2단계: 초기 진압 및 대피", "3단계: 상황 종료"])
    
    with tab1:
        st.markdown("""
        * **상황 발생:** 본관 2층 탕비실 콘센트 단락으로 인한 화재 및 연기 발생
        * **최초 발견자 행동:** **"불이야!"** 크게 3회 외치고 발신기(비상벨) 누름
        * **종합방재실:** 화재 경보 확인 후 전 사내 비상 방송 송출, 119 신고
        """)
    with tab2:
        st.markdown("""
        * **자위소방대 가동:** 
            * **초기소화반:** 인근 소화기 및 옥내소화전 전개, 진압 시도
            * **피난유도반:** 주요 계단 및 비상구 배치, 대원들을 비상계단으로 유도
        * **임직원 대피:** 자세를 낮추고 지정된 대피소로 이동
        """)
    with tab3:
        st.markdown("""
        * **인원 점검:** 대피소 집결 후 팀별 인원 체크 및 피난유도반 보고
        * **소방서 연계:** 소방대원에게 화재 상황 및 미대피자 정보 인계
        """)

    st.markdown("---")
    
    st.subheader("🧯 올바른 소화기 사용법 (P.A.S.S.)")
    st.markdown("""
    1. **P (Pull the pin):** 소화기를 바닥에 내려놓고 **안전핀을 뽑습니다.**
    2. **A (Aim at the base):** 바람을 등지고 소화기 호스를 **불이 난 곳을 향해** 조준합니다.
    3. **S (Squeeze the lever):** 손잡이를 **힘껏 움켜쥡니다.**
    4. **S (Sweep side to side):** 빗자루로 쓸듯 **좌우로 골고루** 분사합니다.
    """)

# ==========================================
# 오른쪽 컬럼 (대피소 안내 및 소방청 소식)
# ==========================================
with col_right:
    st.subheader("🚨 비상 대피소 안내")
    
    # 1차 대피소
    with st.container(border=True):
        st.error("🚩 **1차 대피소 (주 대피소)**")
        st.markdown("**관리동 뒤 쪽문**\n* 건물에서 빠져나와 즉시 집결하여 인원 파악을 실시하는 장소입니다.")
        
        # 파일이 두 가지 이름 형태(shelter1_1.jpg 또는 shelter1_1.jpg.jpg) 중 무엇이든 다 찾도록 보완
        img1_path = os.path.join(BASE_DIR, "shelter1_1.jpg") if os.path.exists(os.path.join(BASE_DIR, "shelter1_1.jpg")) else os.path.join(BASE_DIR, "shelter1_1.jpg.jpg")
        img2_path = os.path.join(BASE_DIR, "shelter1_2.jpg") if os.path.exists(os.path.join(BASE_DIR, "shelter1_2.jpg")) else os.path.join(BASE_DIR, "shelter1_2.jpg.jpg")
        
        if os.path.exists(img1_path):
            st.image(img1_path, caption="1차 대피소 현장 위치 및 전경", use_container_width=True)
        if os.path.exists(img2_path):
            st.image(img2_path, caption="1차 대피소 비상 피난 동선 도면", use_container_width=True)
        if not os.path.exists(img1_path) and not os.path.exists(img2_path):
            st.caption("⚠️ 이미지 파일을 찾을 수 없습니다.")
        
    # 2차 대피소
    with st.container(border=True):
        st.warning("⚠️ **2차 대피소 (지정 대피소)**")
        st.markdown("**셀트리온 정문**\n* 화재 및 누출 규모가 커 대내외 확산 우려가 있을 경우 이동하는 장소입니다.")
        
        img3_path = os.path.join(BASE_DIR, "shelter2.jpg") if os.path.exists(os.path.join(BASE_DIR, "shelter2.jpg")) else os.path.join(BASE_DIR, "shelter2.jpg.jpg")
        
        if os.path.exists(img3_path):
            st.image(img3_path, caption="2차 대피소(셀트리온 정문) 및 설비별 피해 예상 반경", use_container_width=True)
        else:
            st.caption("⚠️ 이미지 파일을 찾을 수 없습니다.")

    st.markdown("---")
    
    st.subheader("📰 소방청 최신 보도자료")
    releases = fetch_nfa_press_releases()
    if releases:
        for rel in releases:
            with st.container(border=True):
                st.markdown(f"📅 **{rel['date']}**")
                st.markdown(f"**[{rel['title']}]({rel['link']})**")
    else:
        st.markdown("[🔗 소방청 보도자료 바로가기](https://www.nfa.go.kr/nfa/news/pressrelease/press/)")

st.markdown("---")
st.caption(f"Copyright 2026. 안전보건관리실. (최종 업데이트: {datetime.now().strftime('%Y-%m-%d')})")