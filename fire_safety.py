# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib3
import os
import xml.etree.ElementTree as ET
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
# 소방/안전 최신 보도자료 수집 함수 (RSS 방식)
# -------------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_safety_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    articles = []
    
    try:
        r = requests.get("https://www.korea.kr/rss/policy.xml", headers=headers, timeout=8, verify=False)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for item in root.findall(".//item"):
                title = item.findtext("title", default="").strip()
                link = item.findtext("link", default="").strip()
                pub_date = item.findtext("pubDate", default="-")
                description = item.findtext("description", default="내용 없음").strip()
                
                if description:
                    soup = BeautifulSoup(description, "html.parser")
                    description = soup.get_text(strip=True)
                
                if len(pub_date) > 16:
                    pub_date = pub_date[:16]

                articles.append({
                    "title": title,
                    "link": link,
                    "date": pub_date,
                    "content": description if description else "본문 요약 정보가 없습니다."
                })
                if len(articles) >= 5:
                    break
    except Exception:
        pass

    return articles

# -------------------------------------------------------------
# 메인 레이아웃 (좌측: 조직도, 검색, 시나리오, 연락망 / 우측: 대피소 및 소식)
# -------------------------------------------------------------
col_left, col_right = st.columns([3, 2])

with col_left:
    # -------------------------------------------------------------
    # 1. 비상대응 조직표 (도식화 모형 구현)
    # -------------------------------------------------------------
    st.subheader("🏢 비상대응 조직표")
    
    with st.expander("🔻 자위소방대 비상대응 조직도 보기 (클릭하여 펼치기)", expanded=True):
        # 최상위: 대장
        st.markdown("<div style='text-align: center; font-weight: bold; background-color: #f0f2f6; padding: 8px; border-radius: 5px; border: 1px solid #dcdcdc;'>👑 대장: CSO (안전보건총괄책임자)</div>", unsafe_allowed_html=True)
        st.markdown("<div style='text-align: center; color: #888;'>│</div>", unsafe_allowed_html=True)
        
        # 중간: 부대장 3인
        c_sub1, c_sub2, c_sub3 = st.columns(3)
        with c_sub1:
            st.markdown("<div style='text-align: center; border: 1px solid #b2bec3; padding: 6px; border-radius: 5px; background-color: #e17055; color: white;'><b>소방지휘 본부대장</b><br><small>기술본부장</small></div>", unsafe_allowed_html=True)
        with c_sub2:
            st.markdown("<div style='text-align: center; border: 1px solid #b2bec3; padding: 6px; border-radius: 5px; background-color: #0984e3; color: white;'><b>상황 통제본부대장</b><br><small>관리본부장</small></div>", unsafe_allowed_html=True)
        with c_sub3:
            st.markdown("<div style='text-align: center; border: 1px solid #b2bec3; padding: 6px; border-radius: 5px; background-color: #00b894; color: white;'><b>의료구호본부대장</b><br><small>사업본부장</small></div>", unsafe_allowed_html=True)
            
        st.markdown("<div style='text-align: center; color: #888;'>│</div>", unsafe_allowed_html=True)
        
        # 하부: 반별 세부 조직
        b1, b2, b3, b4, b5, b6, b7, b8 = st.columns(8)
        
        with b1:
            st.caption("**지휘반**")
            st.markdown("<small>안전환경팀</small>", unsafe_allowed_html=True)
        with b2:
            st.caption("**훈련/소화반**")
            st.markdown("<small>기계팀,<br>운영팀</small>", unsafe_allowed_html=True)
        with b3:
            st.caption("**피난유도반**")
            st.markdown("<small>계전팀,<br>네트워크팀</small>", unsafe_allowed_html=True)
        with b4:
            st.caption("**비상연락반**")
            st.markdown("<small>경영기획팀</small>", unsafe_allowed_html=True)
        with b5:
            st.caption("**경계반**")
            st.markdown("<small>기획재무팀,<br>DX혁신팀</small>", unsafe_allowed_html=True)
        with b6:
            st.caption("**의료반**")
            st.markdown("<small>ESG추진팀</small>", unsafe_allowed_html=True)
        with b7:
            st.caption("**후송반**")
            st.markdown("<small>대외협력팀</small>", unsafe_allowed_html=True)
        with b8:
            st.caption("**방호/복구반**")
            st.markdown("<small>고객지원팀</small>", unsafe_allowed_html=True)
            
        st.markdown("---")
        st.markdown("##### 🌙 야간 및 공휴일 비상대응 조직 (총원: 6명)")
        st.caption("※ 교대근무자 5명 + 경비원 1명")
        
        st.markdown("<div style='text-align: center; font-weight: bold; background-color: #dfe6e9; padding: 6px; border-radius: 5px;'>임시소방대장 : 운영그룹장 (1명)</div>", unsafe_allowed_html=True)
        st.markdown("<div style='text-align: center; color: #888;'>│</div>", unsafe_allowed_html=True)
        
        n1, n2, n3 = st.columns(3)
        with n1:
            st.info("**비상연락반**\n\nCCR근무자 (2명)")
        with n2:
            st.warning("**소화반**\n\n현장근무자 (2명)")
        with n3:
            st.success("**소방대유도반**\n\n경비원 (1명)")

    st.markdown("---")

    # -------------------------------------------------------------
    # 2. 나의 자위소방대 임무 찾기
    # -------------------------------------------------------------
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
    # 3. 25년 하반기 소방훈련 세부 시나리오 (4개 탭)
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
    
    # -------------------------------------------------------------
    # 4. 사고대응 유관기관 비상연락체계 (신규 섹션)
    # -------------------------------------------------------------
    st.subheader("📞 사고대응 유관기관 비상연락체계")
    
    contact_data = [
        {"구분": "정부", "명칭(담당자)": "신산업 분산에너지과", "전화번호": "044-203-3927", "비고": "산업통상자원부"},
        {"구분": "정부", "명칭(담당자)": "중부지방고용노동청", "전화번호": "032-460-6248", "비고": "고용노동부"},
        {"구분": "정부", "명칭(담당자)": "중대산업사고예방센터", "전화번호": "031-364-7508", "비고": "고용노동부"},
        {"구분": "정부", "명칭(담당자)": "시흥화학재난합동방재센터", "전화번호": "031-470-2454", "비고": ""},
        {"구분": "한국에너지공단", "명칭(담당자)": "분산에너지실", "전화번호": "010-5589-3342", "비고": ""},
        {"구분": "유관기관", "명칭(담당자)": "산업안전보건공단 인천광역본부", "전화번호": "032-510-0500", "비고": ""},
        {"구분": "유관기관", "명칭(담당자)": "인천광역시 안전상황실", "전화번호": "032-440-1881", "비고": ""},
        {"구분": "유관기관", "명칭(담당자)": "연수구청 재난안전본부", "전화번호": "080-040-3650", "비고": ""},
        {"구분": "유관기관", "명칭(담당자)": "송도 119안전센터", "전화번호": "032-810-6683", "비고": ""},
        {"구분": "유관기관", "명칭(담당자)": "경찰민원 콜센터", "전화번호": "182", "비고": ""},
        {"구분": "유관기관", "명칭(담당자)": "송도국제도시 지구대", "전화번호": "032-822-1112", "비고": ""},
        {"구분": "유관기관", "명칭(담당자)": "한국가스공사 인천지역본부", "전화번호": "주간) 032-453-6637\n야간) 032-453-6555", "비고": ""},
        {"구분": "유관기관", "명칭(담당자)": "한국가스안전공사 인천본부", "전화번호": "032-435-1525", "비고": ""},
        {"구분": "유관기관", "명칭(담당자)": "한국전기안전공사 인천본부", "전화번호": "032-290-7000", "비고": ""},
        {"구분": "유관기관", "명칭(담당자)": "한국전력 송도변전소", "전화번호": "031-363-5356", "비고": ""},
        {"구분": "유관기관", "명칭(담당자)": "삼천리 종합상황실", "전화번호": "080-3002-118", "비고": ""},
        {"구분": "인근사업장", "명칭(담당자)": "셀트리온", "전화번호": "032-850-5119", "비고": ""},
        {"구분": "인근사업장", "명칭(담당자)": "공영차고지", "전화번호": "032-814-0900", "비고": ""},
        {"구분": "인근사업장", "명칭(담당자)": "송도하수처리장", "전화번호": "032-899-4658", "비고": ""},
        {"구분": "인근사업장", "명칭(담당자)": "KD Corporation", "전화번호": "031-499-0815", "비고": ""},
        {"구분": "협력업체", "명칭(담당자)": "이우현 소장", "전화번호": "010-2310-9417", "비고": "소장"},
        {"구분": "협력업체", "명칭(담당자)": "신재을 팀장", "전화번호": "010-6220-0913", "비고": "기계 관리감독자"},
        {"구분": "협력업체", "명칭(담당자)": "신명규 팀장", "전화번호": "010-8501-4325", "비고": "전기 관리감독자"},
        {"구분": "협력업체", "명칭(담당자)": "김요한 팀장", "전화번호": "010-4109-5114", "비고": "계전 관리감독자"},
    ]
    
    df_contacts = pd.DataFrame(contact_data)
    
    # 구분별로 빠르게 검색/필터링할 수 있는 옵션 제공
    selected_category = st.selectbox("📂 구분별 필터 보기", ["전체 보기", "정부", "한국에너지공단", "유관기관", "인근사업장", "협력업체"])
    
    if selected_category != "전체 보기":
        filtered_df = df_contacts[df_contacts["구분"] == selected_category]
    else:
        filtered_df = df_contacts

    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

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
    
    # -------------------------------------------------------------
    # 보도자료 수집
    # -------------------------------------------------------------
    st.subheader("📰 최신 소방/안전 보도자료")
    releases = fetch_safety_news()
    if releases:
        for rel in releases:
            with st.expander(f"📌 {rel['title']}"):
                st.caption(f"📅 등록일: {rel['date']}")
                st.info(rel['content'])
                st.markdown(f"🔗 [원문 기사/보도자료 바로가기]({rel['link']})")
    else:
        st.markdown("[🔗 소방청 보도자료 바로가기](https://www.nfa.go.kr/nfa/news/pressrelease/press/)")

st.markdown("---")
st.caption(f"Copyright 2026. 안전보건관리실. (최종 업데이트: {datetime.now().strftime('%Y-%m-%d')})")
