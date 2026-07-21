# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib3
import os
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="사내 소방안전관리 대시보드", layout="wide", page_icon="🚒")
st.title("🚒 사내 소방안전관리 대시보드")
st.markdown("---")

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."

# 캐시 방지를 위해 cache_data 비활성화하여 즉시 파일 읽기 진행
def get_roster_data():
    # 현재 폴더 및 하위 폴더의 모든 xlsx 파일 검색
    files_in_dir = [f for f in os.listdir(BASE_DIR) if f.endswith('.xlsx')]
    
    excel_path = os.path.join(BASE_DIR, "자위소방대_명단.xlsx")
    
    if not os.path.exists(excel_path):
        # 대안: 한글 파일명 인식 문제 대비 첫 번째 xlsx 파일 읽기
        if files_in_dir:
            excel_path = os.path.join(BASE_DIR, files_in_dir[0])
        else:
            st.error(f"🚨 [파일 읽기 실패] 현재 폴더에서 `.xlsx` 엑셀 파일을 찾을 수 없습니다. (현재 폴더 파일 목록: {os.listdir(BASE_DIR)})")
            return pd.DataFrame()

    try:
        df = pd.read_excel(excel_path, engine='openpyxl')
        # 열 이름 전처리
        df.columns = [str(c).strip() for c in df.columns]
        if "이름" in df.columns:
            df["이름"] = df["이름"].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"🚨 [엑셀 파일 오류] 파일을 읽는 중 에러 발생: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def fetch_nfa_press_releases():
    url = "https://www.nfa.go.kr/nfa/news/pressrelease/press/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        if r.status_code != 200: return []
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
                    if len(articles) >= 5: break
        return articles
    except Exception: return []

col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("🔍 나의 자위소방대 임무 찾기")
    search_name = st.text_input("본인 이름을 입력하고 Enter를 누르세요.", placeholder="예: 김유리, 전태현")
    
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
    st.subheader("📋 2025년도 소방훈련 시나리오")
    tab1, tab2, tab3 = st.tabs(["1단계: 화재 발생 및 전파", "2단계: 초기 진압 및 대피", "3단계: 상황 종료"])
    with tab1: st.markdown("* **상황 발생:** 본관 2층 탕비실 화재 발생\n* **최초 발견자 행동:** **\"불이야!\"** 3회 외치고 비상벨 누름\n* **종합방재실:** 사내 비상 방송 송출, 119 신고")
    with tab2: st.markdown("* **자위소방대 가동:** 초기소화반(진압 시도), 피난유도반(비상구 배치 및 유도)\n* **임직원 대피:** 자세를 낮추고 지정된 대피소로 이동")
    with tab3: st.markdown("* **인원 점검:** 대피소 집결 후 팀별 인원 체크\n* **소방서 연계:** 소방대원에게 상황 및 미대피자 정보 인계")

    st.markdown("---")
    st.subheader("🧯 올바른 소화기 사용법 (P.A.S.S.)")
    st.markdown("1. **P (Pull the pin):** 안전핀을 뽑습니다.\n2. **A (Aim at the base):** 불이 난 곳을 향해 조준합니다.\n3. **S (Squeeze the lever):** 손잡이를 힘껏 움켜쥡니다.\n4. **S (Sweep side to side):** 좌우로 골고루 분사합니다.")

with col_right:
    st.subheader("🚨 비상 대피소 안내")
    with st.container(border=True):
        st.error("🚩 **1차 대피소 (주 대피소)**")
        st.markdown("**관리동 뒤 쪽문**\n* 건물에서 빠져나와 즉시 집결하여 인원 파악을 실시하는 장소입니다.")
        
        img1_path = os.path.join(BASE_DIR, "shelter1_1.jpg") if os.path.exists(os.path.join(BASE_DIR, "shelter1_1.jpg")) else os.path.join(BASE_DIR, "shelter1_1.jpg.jpg")
        img2_path = os.path.join(BASE_DIR, "shelter1_2.jpg") if os.path.exists(os.path.join(BASE_DIR, "shelter1_2.jpg")) else os.path.join(BASE_DIR, "shelter1_2.jpg.jpg")
        
        if os.path.exists(img1_path): st.image(img1_path, caption="1차 대피소 현장 위치 및 전경", use_container_width=True)
        if os.path.exists(img2_path): st.image(img2_path, caption="1차 대피소 비상 피난 동선 도면", use_container_width=True)
        
    with st.container(border=True):
        st.warning("⚠️ **2차 대피소 (지정 대피소)**")
        st.markdown("**셀트리온 정문**\n* 화재 및 누출 규모가 커 대내외 확산 우려가 있을 경우 이동하는 장소입니다.")
        
        img3_path = os.path.join(BASE_DIR, "shelter2.jpg") if os.path.exists(os.path.join(BASE_DIR, "shelter2.jpg")) else os.path.join(BASE_DIR, "shelter2.jpg.jpg")
        if os.path.exists(img3_path): st.image(img3_path, caption="2차 대피소(셀트리온 정문) 및 피해 예상 반경", use_container_width=True)

    st.markdown("---")
    st.subheader("📰 소방청 최신 보도자료")
    releases = fetch_nfa_press_releases()
    if releases:
        for rel in releases:
            with st.container(border=True):
                st.markdown(f"📅 **{rel['date']}**\n**[{rel['title']}]({rel['link']})**")
    else:
        st.markdown("[🔗 소방청 보도자료 바로가기](https://www.nfa.go.kr/nfa/news/pressrelease/press/)")

st.markdown("---")
st.caption(f"Copyright 2026. 안전보건관리실. (최종 업데이트: {datetime.now().strftime('%Y-%m-%d')})")
