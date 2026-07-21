# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib3
import os
from datetime import datetime

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 페이지 기본 설정
st.set_page_config(page_title="사내 소방안전관리 대시보드", layout="wide", page_icon="🚒")
st.title("🚒 사내 소방안전관리 대시보드")
st.markdown("---")

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."

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
            st.error("🚨 명단 파일을 찾을 수 없습니다.")
            return pd.DataFrame()

        df.columns = [str(c).strip() for c in df.columns]
        if "이름" in df.columns:
            df["이름"] = df["이름"].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"🚨 [파일 읽기 오류] {e}")
        return pd.DataFrame()

# -------------------------------------------------------------
# 소방청 보도자료 크롤링 함수
# -------------------------------------------------------------
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

# -------------------------------------------------------------
# 메인 레이아웃 (좌측: 검색 및 시나리오 / 우측: 대피소 및 소식)
# -------------------------------------------------------------
col_left, col_right = st.columns([3, 2])

with col_left:
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
    
    # -------------------------------------------------------------
    # 25년 하반기 소방훈련 세부 시나리오 (4개 탭)
    # -------------------------------------------------------------
    st.subheader("📋 25년 하반기 소방훈련 세부 시나리오")
    st.caption("🚨 **상황:** 정문 주차장 급속충전 중인 전기차량('코나') 화재 발생")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "1단계: 화재발생 & 신고", 
        "2단계: 초기소화 & 대피", 
        "3단계: 소방차 유도 & 강평",
        "🖼️ 참고: 이미지로 확인하기"
    ])
    
    with tab1:
        st.markdown("##### 📢 상황 인지 및 소내 전파 (14:00 ~ 14:04)")
        scenario_data_1 = [
            {"시간": "14:00~14:02", "담당자": "로컬근무자 ➡ CCR", "조치내용": "급속충전 중인 전기차 화재 목격 및 CCR 상황전파 (\"불이야! 불이야!\")", "비고": "연막탄 6EA 세팅, 사이렌 송출"},
            {"시간": "14:02", "담당자": "운영리더", "조치내용": "화재발생 상황 소내 전파 및 CO에게 소방서 신고 지시", "비고": "-"},
            {"시간": "14:02", "담당자": "운전원 (CO)", "조치내용": "119 소방서 화재 신고 (인천종합에너지 정문 주차장 전기차 화재)", "비고": "-"},
            {"시간": "14:04", "담당자": "비상연락반 (경영지원팀)", "조치내용": "페이지폰 소내 대피 방송 실시 (2회)", "비고": "-"},
        ]
        st.table(pd.DataFrame(scenario_data_1))

    with tab2:
        st.markdown("##### 🧯 초기소화 및 전직원 대피 (14:02 ~ 14:10)")
        scenario_data_2 = [
            {"시간": "14:02~14:05", "담당자": "훈련 및 소화반 (운영/기계)", "조치내용": "옥외소화전함 개방, 호스 전개/연결 및 방수 위치 확보 후 방수 실시", "비고": "약 1분간 방사"},
            {"시간": "14:05", "담당자": "피난유도반 (계전팀)", "조치내용": "각 층 비상계단 대피 유도 및 잔류자 확인 후 최종 퇴실", "비고": "층별 담당자 지정"},
            {"시간": "14:05~14:10", "담당자": "전직원", "조치내용": "1차 대피소(1층 정문)로 신속 대피, 팀별 인원 체크 후 소방안전관리자 보고", "비고": "대피 완료 후 시연 관람"},
            {"시간": "14:05~14:10", "담당자": "소화반", "조치내용": "충전기 옆 질식포 보관함에서 질식포 수령 후 화재차량 질식소화 전개", "비고": "화염 추가확산 방지"},
        ]
        st.table(pd.DataFrame(scenario_data_2))

    with tab3:
        st.markdown("##### 🚒 모의소방차 진입 및 훈련 종료 (14:10 ~ 14:15)")
        scenario_data_3 = [
            {"시간": "14:10~14:11", "담당자": "방호 및 복구반 (네트워크팀)", "조치내용": "모의소방차 진입 요청 및 정문/주차장 진입 유도 (유도자 2인 배치)", "비고": "진입 완료 시 상황 종료"},
            {"시간": "14:11~14:15", "담당자": "소방안전관리자 (김유리)", "조치내용": "안전보건총괄책임자에게 대피인원 및 피해상황 보고", "비고": "-"},
            {"시간": "14:11~14:15", "담당자": "자위소방대장 / 119안전센터", "조치내용": "훈련 실시 완료 보고 및 신송119안전센터 최종 훈련 강평", "비고": "피드백 차후 적용"},
        ]
        st.table(pd.DataFrame(scenario_data_3))

    with tab4:
        st.markdown("##### 📄 원본 세부 시나리오 문서 이미지")
        
        # 띄어쓰기 파일명('fire drill_1.jpg')과 언더바 파일명('fire_drill_1.jpg') 둘 다 자동 검색
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
                st.image(found_path, caption=caption, use_container_width=True)
                st.markdown("---")
            else:
                st.warning(f"📷 `{file_candidates[0]}` 이미지 파일이 올라오면 이곳에 **[{caption}]** 이미지가 표시됩니다.")

    st.markdown("---")
    st.subheader("🧯 올바른 소화기 사용법 (P.A.S.S.)")
    st.markdown("1. **P (Pull the pin):** 안전핀을 뽑습니다.\n2. **A (Aim at the base):** 불이 난 곳을 향해 조준합니다.\n3. **S (Squeeze the lever):** 손잡이를 힘껏 움켜쥡니다.\n4. **S (Sweep side to side):** 좌우로 골고루 분사합니다.")

with col_right:
    st.subheader("🚨 비상 대피소 안내")
    with st.container(border=True):
        st.error("🚩 **1차 대피소 (주 대피소)**")
        st.markdown("**관리동 1층 정문 (훈련 집결지)**\n* 건물에서 빠져나와 즉시 집결하여 팀별 인원 파악을 실시하는 장소입니다.")
        
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
