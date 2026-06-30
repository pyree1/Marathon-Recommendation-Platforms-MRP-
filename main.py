import streamlit as st
import pandas as pd
import os
import math
from db_manager import init_db
from scraper import crawl_marathon_schedule

# DB 초기화
init_db()

# 페이지 설정
st.set_page_config(page_title="대한민국 마라톤 매칭 플랫폼", layout="wide")
# main.py 파일 상단부 (st.set_page_config 바로 아래에 배치)

# ─── 🔑 세션 상태(Session State) 초기화 블록 ───
if 'survey_active' not in st.session_state: st.session_state.survey_active = False
if 'survey_step' not in st.session_state: st.session_state.survey_step = 1
if 'show_popup' not in st.session_state: st.session_state.show_popup = False

# 퀴즈 상태 머신 임시 변수
if 'tmp_concept' not in st.session_state: st.session_state.tmp_concept = "🌍 상관없음 (전체)"
if 'tmp_style' not in st.session_state: st.session_state.tmp_style = "ALL (전체)"
if 'tmp_distances' not in st.session_state: st.session_state.tmp_distances = ["10K"]
if 'tmp_scale' not in st.session_state: st.session_state.tmp_scale = "ALL (전체)"
if 'tmp_max_fee' not in st.session_state: st.session_state.tmp_max_fee = 120000

# 확정 반영용 필터 스토리지
if 'rec_concept' not in st.session_state: st.session_state.rec_concept = "🌍 상관없음 (전체)"
if 'rec_style' not in st.session_state: st.session_state.rec_style = "ALL (전체)"
if 'rec_scale' not in st.session_state: st.session_state.rec_scale = "ALL (전체)"
if 'rec_distances' not in st.session_state: st.session_state.rec_distances = []
if 'max_fee' not in st.session_state: st.session_state.max_fee = 150000
# ───────────────────────────────────────────────
# 고급 CSS 주입 (귀여우면서 직관적인 MZ 스타일 및 애니메이션 배지)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gmarket+Sans:wght@500;700&display=swap');
    
    .section-title-large {
        font-size: 30px !important;
        font-weight: 900 !important;
        color: #1E3A8A;
        margin-top: 10px;
        margin-bottom: 15px;
        border-left: 8px solid #FBBF24;
        padding-left: 14px;
    }
    .status-badge {
        font-size: 15px !important;
        font-weight: 800;
        padding: 5px 12px;
        border-radius: 20px;
        display: inline-block;
    }
    .status-upcoming { background-color: #DBEAFE; color: #1E40AF; }
    .status-open { background-color: #D1FAE5; color: #065F46; }
    .status-closed { background-color: #FEE2E2; color: #991B1B; }
    
    .hashtag {
        background-color: #EFF6FF;
        color: #2563EB;
        padding: 4px 12px;
        border-radius: 30px;
        font-size: 13px;
        font-weight: 700;
        margin-right: 6px;
        display: inline-block;
        border: 1px solid #BFDBFE;
    }
    .theme-badge {
        background-color: #FEF3C7;
        color: #D97706;
        padding: 5px 12px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 800;
        display: inline-block;
        border: 1px solid #FCD34D;
        margin-bottom: 8px;
    }
    .link-btn {
        display: inline-block;
        background-color: #3B82F6;
        color: white !important;
        padding: 8px 16px;
        border-radius: 6px;
        text-decoration: none !important;
        font-size: 14px;
        font-weight: bold;
        margin-top: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .link-btn:hover { background-color: #1D4ED8; }

    /* 💡 개선 포인트 1: 상단 '3초 만에 찾기' / '전체 보기' 버튼을 더 크고 눈에 띄게 */
    div[class*="st-key-top_action_buttons"] button {
        font-size: 20px !important;
        font-weight: 800 !important;
        padding: 18px 22px !important;
        height: auto !important;
        border-radius: 12px !important;
    }
    div[class*="st-key-top_action_buttons"] button p {
        font-size: 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

def calculate_distance(lat1, lon1, lat2, lon2):
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return 9999
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 💡 개선 포인트 2: 타이틀을 부드러운 텍스트로 중앙 정렬
st.markdown("<h1 style='text-align: center; color: #2563EB; font-weight: 900; margin-bottom: 30px;'>🏃‍♂️ 전국 마라톤 핏-체킹 플랫폼</h1>", unsafe_allow_html=True)

# 이 부분을 기존의 데이터 로딩 코드 자리에 넣으세요.
@st.cache_data
def load_data():
    if os.path.exists('data/marathons.csv'):
        df = pd.read_csv('data/marathons.csv')
        # 혹시 모를 컬럼 누락 방지 (date 컬럼이 없으면 새로 생성)
        if 'date' not in df.columns:
            new_df = crawl_marathon_schedule()
            os.makedirs('data', exist_ok=True)
            new_df.to_csv('data/marathons.csv', index=False)
            return new_df
        return df
    else:
        # 파일이 없으면 새로 생성 후 반환
        new_df = crawl_marathon_schedule()
        os.makedirs('data', exist_ok=True)
        new_df.to_csv('data/marathons.csv', index=False)
        return new_df

# 함수 호출하여 데이터 할당
df = load_data()

# 포스터 컬럼 예외 처리
if 'poster' not in df.columns:
    df['poster'] = "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?w=150&q=80" # 기본 이미지

# =======================================================================
# 📍 대한민국 주요 시/도 및 시/군/구 중심 좌표 정의
# =======================================================================
REGION_COORDS = {
    "서울특별시": {"전체": (37.5665, 126.9780)},
    "경기도": {"수원시": (37.2636, 127.0286), "성남시": (37.4200, 127.1265), "고양시": (37.6584, 126.8320), "용인시": (37.2410, 127.1775), "부천시": (37.5034, 126.7660)},
    "인천광역시": {"전체": (37.4563, 126.7052)},
    "강원특별자치도": {"춘천시": (37.8813, 127.7300), "강릉시": (37.7519, 128.8761), "원주시": (37.3422, 127.9201)},
    "충청남도": {"천안시": (36.8143, 127.1493), "아산시": (36.7862, 127.0041), "당진시": (36.8927, 126.6283), "서산시": (36.7845, 126.4503)},
    "충청북도": {"청주시": (36.6372, 127.4897), "충주시": (36.9910, 127.9259)},
    "대전광역시": {"전체": (36.3504, 127.3845)},
    "세종특별자치시": {"전체": (36.4801, 127.2890)},
    "전북특별자치도": {"전주시": (35.8242, 127.1480), "군산시": (35.9677, 126.7366), "익산시": (35.9482, 126.9573)},
    "전라남도": {"목포시": (34.8118, 126.3922), "여수시": (34.7604, 127.6622), "순천시": (34.9506, 127.4872)},
    "광주광역시": {"전체": (35.1595, 126.8526)},
    "경상북도": {"포항시": (36.0190, 129.3435), "경주시": (35.8562, 129.2132), "구미시": (36.1195, 128.3443)},
    "경상남도": {"창원시": (35.2281, 128.6811), "김해시": (35.2285, 128.8894), "진주시": (35.1713, 128.0568)},
    "대구광역시": {"전체": (35.8714, 128.6014)},
    "부산광역시": {"전체": (35.1796, 129.0756)},
    "울산광역시": {"전체": (35.5389, 129.3114)},
    "제주특별자치도": {"제주시": (33.4996, 126.5312), "서귀포시": (33.2541, 126.5601)}
}

# ─── 🧭 좌측 UI 전면 개편: 심플한 위치 설정 및 거리 필터 ───
st.sidebar.markdown("### 📍 내 위치 기반 검색")

# 1. 위치 설정 방식 안내 및 수동 선택
st.sidebar.info("지도에 내 위치(GPS)를 띄우려면 브라우저 팝업에서 **위치 허용**을 눌러주세요. 거리 검색은 아래 지정한 지역을 기준으로 작동합니다.")

selected_do = st.sidebar.selectbox("🗺️ 시/도 선택", list(REGION_COORDS.keys()), index=0)
selected_si = st.sidebar.selectbox("🗺️ 시/군/구 선택", list(REGION_COORDS[selected_do].keys()), index=0)

# 선택된 지역 좌표 할당 및 전체 데이터 거리 재계산
USER_BASE_LAT, USER_BASE_LNG = REGION_COORDS[selected_do][selected_si]
df['distance_km'] = df.apply(lambda r: calculate_distance(USER_BASE_LAT, USER_BASE_LNG, r['lat'], r['lng']), axis=1)

# 2. 반경 거리 제한 슬라이더
distance_limit = st.sidebar.slider(f"🎯 [{selected_si}] 기준 반경 (km)", 10, 500, 200, 10)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 추가 조건 필터")
selected_status = st.sidebar.selectbox("🚦 모집 진행 상황", options=["전체"] + sorted(df['status'].unique().tolist()))

# --- 데이터 필터링 파이프라인 ---
filtered_df = df.copy()

# 1차 필터링: 반경 거리 및 상태
filtered_df = filtered_df[filtered_df['distance_km'] <= distance_limit]
if selected_status != "전체": 
    filtered_df = filtered_df[filtered_df['status'] == selected_status]

# 2차 필터링: 팝업 퀴즈(설문) 결과 연동
@st.dialog("🎯 나만의 마라톤 핏(Fit) 찾기 초스피드 Quiz")
def show_survey_popup():
    step = st.session_state.survey_step
    
    st.progress(step / 5.0, text=f"**현재 {step}단계 진행 중 / 총 5단계**")
    st.markdown("---")
    
    if step == 1:
        st.markdown("#### **🎉 Q1. 어떤 테마/컨셉의 대회를 선호하시나요?**")
        st.session_state.tmp_concept = st.radio("지루한 러닝은 거부한다! 당신의 취향은?", ["🌍 상관없음 (전체 다 볼래요!)", "🥳 펀런 앤 페스티벌! (무도런/나는솔로런 같은 이색 이벤트)", "⛰️ 자연 속 야생 날것의 매력! (산악 트레일런)", "⏱️ 클래식 도심 레이서! (전통 시티/강변 코스)"], index=0)
    elif step == 2:
        st.markdown("#### **🏁 Q2. 이번에 목표로 하는 타겟 코스는 무엇인가요?**")
        st.session_state.tmp_distances = st.multiselect("다중 선택 가능", ["5K", "10K", "Half", "Full", "장거리 (60km 이상)"], default=st.session_state.tmp_distances)
    elif step == 3:
        st.markdown("#### **👥 Q3. 대회장 인파 및 인프라 규모는 어느 정도가 좋으세요?**")
        st.session_state.tmp_scale = st.radio("축제 규모 픽하기", ["ALL (전체)", "대규모 (1만명 이상)", "중규모 (3천명~1만명)", "소규모 (3천명 미만)"], index=0)
    elif step == 4:
        st.markdown("#### **⚡ Q4. 본인의 페이스 조절 및 난이도 성향은?**")
        st.session_state.tmp_style = st.radio("러닝 스타일 결정", ["ALL (전체)", "초보 러너 (완주 목표)", "PB 도전 (기록 달성)"], index=0)
    elif step == 5:
        st.markdown("#### **💰 Q5. 지갑 사정을 고려한 참가비 상한선은?**")
        st.session_state.tmp_max_fee = st.slider("최대 허용 참가비(원)", 30000, 150000, st.session_state.tmp_max_fee, 5000)

    st.markdown("<br>", unsafe_allow_html=True)
    
    b_col1, b_col2 = st.columns([1, 1])
    with b_col1:
        if step > 1 and st.button("⬅️ 이전 단계", use_container_width=True):
            st.session_state.survey_step -= 1
            st.rerun()
    with b_col2:
        if step < 5:
            if st.button("다음 단계로 ➡️", use_container_width=True):
                st.session_state.survey_step += 1
                st.rerun()
        else:
            if st.button("🏁 나만의 맞춤대회 찾기!", type="primary", use_container_width=True):
                st.session_state.rec_concept = st.session_state.tmp_concept
                st.session_state.rec_distances = st.session_state.tmp_distances
                st.session_state.rec_scale = st.session_state.tmp_scale
                st.session_state.rec_style = st.session_state.tmp_style
                st.session_state.max_fee = st.session_state.tmp_max_fee
                st.session_state.survey_active = True
                st.session_state.show_popup = False
                st.session_state.survey_step = 1
                st.rerun()

with st.container(key="top_action_buttons"):
    c_pop1, c_pop2 = st.columns([2, 1])
    with c_pop1:
        if st.button("🎯 3초 만에 나만의 맞춤 대회 찾기", type="primary", use_container_width=True):
            st.session_state.survey_step = 1
            st.session_state.show_popup = True
            st.rerun()
    with c_pop2:
        if st.button("🌐 핏(Fit) 조건 해제", use_container_width=True):
            st.session_state.survey_active = False
            st.rerun()

if st.session_state.show_popup:
    show_survey_popup()

if st.session_state.survey_active:
    if "상관없음" not in st.session_state.rec_concept:
        if "펀런" in st.session_state.rec_concept:
            filtered_df = filtered_df[filtered_df['theme'].str.contains('이벤트|축제|이색|커플|이색대회', na=False)]
        elif "야생" in st.session_state.rec_concept:
            filtered_df = filtered_df[filtered_df['theme'].str.contains('트레일|산악|챌린지|울트라', na=False)]
        elif "클래식" in st.session_state.rec_concept:
            filtered_df = filtered_df[~filtered_df['theme'].str.contains('이벤트|축제|이색|트레일|산악', na=False)]
            
    if st.session_state.rec_style != "ALL (전체)":
        filtered_df = filtered_df[filtered_df['style'] == st.session_state.rec_style]
    if st.session_state.rec_scale != "ALL (전체)":
        filtered_df = filtered_df[filtered_df['scale'] == st.session_state.rec_scale]
    
    filtered_df = filtered_df[filtered_df['fee_numeric'] <= st.session_state.max_fee]
    
    if st.session_state.rec_distances:
        def match_distance(course_str):
            for dist in st.session_state.rec_distances:
                if dist.lower() in course_str.lower(): return True
            return False
        filtered_df = filtered_df[filtered_df['course'].apply(match_distance)]

filtered_df = filtered_df.sort_values(by='date')

st.markdown("---")
all_filtered_titles = ["🔍 지도를 보고 관심 있는 대회를 선택해보세요 (전체 보기)"] + filtered_df['title'].tolist()
selected_map_title = st.selectbox("📍 지도 연동 내비게이터 (클릭한 대회를 리스트에 고정하려면 선택하세요)", options=all_filtered_titles, index=0)

if selected_map_title != "🔍 지도를 보고 관심 있는 대회를 선택해보세요 (전체 보기)":
    filtered_df = filtered_df[filtered_df['title'] == selected_map_title]

if st.session_state.survey_active:
    st.info(f"✨ 핏-체킹 퀴즈 필터 연동 중: [컨셉: {st.session_state.rec_concept.split('(')[0]}] | [{st.session_state.rec_style}] | [{st.session_state.rec_scale}] | 최고 참가비 {st.session_state.max_fee:,}원 이하")

# ─── 메인 뷰 스플릿 레이아웃 ───
col_list, col_map = st.columns([1.5, 1.0])

with col_list:
    view_type = "🎯 맞춤 매칭 결과" if st.session_state.survey_active else "🌐 대한민국 전체 대회"
    st.markdown(f'<div class="section-title-large">{view_type} ({len(filtered_df)}건)</div>', unsafe_allow_html=True)
    # [수정 시작] 데이터 루프 돌기 직전에 http를 https로 강제 변환
    filtered_df['poster'] = filtered_df['poster'].str.replace('http://', 'https://', regex=False)
    filtered_df['link'] = filtered_df['link'].str.replace('http://', 'https://', regex=False)
    
    if filtered_df.empty:
        st.warning("앗! 조건에 딱 들어맞는 대회가 아쉽게도 없습니다.")
    else:
        with st.container(height=650):  
            for _, row in filtered_df.iterrows():
                with st.container(border=True):
                    card_img, card_left, card_right = st.columns([0.8, 2.1, 1.1])
                    
                    with card_img:
                        # 💡 이미지 포스터가 없을 때를 대비한 꼼꼼한 체크
                        poster_url = row['poster'] if pd.notnull(row['poster']) else "https://via.placeholder.com/300x200"
                        if 'image_url' in filtered_df.columns:
                            filtered_df['image_url'] = filtered_df['image_url'].str.replace('http://', 'https://')
                        if poster_url and isinstance(poster_url, str) and poster_url.startswith('http'):
                          try:
                              st.image(poster_url, use_container_width=True)
                          except:
                                st.markdown("<div style='text-align:center; padding:20px;'>이미지 없음</div>", unsafe_allow_html=True)
                        else:
                            # 이미지가 없거나 잘못된 경로일 경우 대신 표시할 HTML
                            st.markdown("""
                                 <div style="height: 150px; display: flex; align-items: center; justify-content: center; 
                                 background-color: #f0f0f0; border-radius: 10px; color: #888;">
                                  이미지 준비 중
                                 </div>
                             """, unsafe_allow_html=True)
                    
                    with card_left:
                        st.markdown(f"<div class='theme-badge'>{row['theme']}</div>", unsafe_allow_html=True)
                        st.markdown(f"### **{row['title']}**")
                        
                        course_tags = [c.strip() for c in row['course'].split(',')]
                        tags_html = f"<span class='hashtag'>#{row['style'].split()[0]}</span><span class='hashtag'>#{row['scale'].split()[0]}</span>"
                        for tag in course_tags:
                            tags_html += f"<span class='hashtag'>#{tag}</span>"
                        st.markdown(tags_html, unsafe_allow_html=True)
                        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)
                        
                        st.markdown(f"📅 **접수기간 :** {row['period']}")
                        st.markdown(f"💰 **참가비 :** `{row['fee']}`")
                        st.markdown(f"🏁 코스인덱스: `{row['course']}` | 🧭 거점 거리 **{row['distance_km']:.1f} km**")
                    
                    with card_right:
                        status_map = {"접수예정": "status-upcoming", "접수중": "status-open", "접수마감": "status-closed"}
                        s_class = status_map.get(row['status'], "status-open")
                        
                        st.markdown(
                            f"""
                            <div style="text-align: right; padding-top: 5px;">
                                <span class="status-badge {s_class}">{row['status']}</span>
                                <br><br>
                                <span style="font-size: 14px; font-weight: bold; color: #1E3A8A;">📅 개최: {row['date']}</span>
                                <br>
                                <span style="font-size: 18px; font-weight: 900; color: #10B981;">📍 {row['location']}</span>
                                <br><br>
                                <a href="{row['link']}" target="_blank" rel="noopener noreferrer" class="link-btn">🔗 공식 접수처</a>
                                <br>
                                <span style="font-size: 10px; color: #94A3B8; word-break: break-all;">접속 안되면 길게 눌러 복사 → {row['link']}</span>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )

with col_map:
    st.markdown('<div class="section-title-large">📍 전국 맵 락인</div>', unsafe_allow_html=True)
    
    # 1. 마커 데이터 생성
    marker_js = ""
    for _, row in filtered_df.iterrows():
        if pd.notna(row.get('lat')) and pd.notna(row.get('lng')):
            marker_js += f"""
                var markerPos = new kakao.maps.LatLng({row['lat']}, {row['lng']});
                var marker = new kakao.maps.Marker({{ position: markerPos }});
                marker.setMap(map);
                
                var infowindow = new kakao.maps.InfoWindow({{
                    content: '<div style="padding:5px; font-size:12px;">{row.get("title", "대회")}</div>'
                }});
                kakao.maps.event.addListener(marker, 'click', function() {{ infowindow.open(map, marker); }});
            """

    # 2. 지도 HTML (https 강제)
    map_html = f"""
        <div id="map" style="width:100%; height:550px; border-radius:15px;"></div>
        <script type="text/javascript" src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=e265c9f38550c96c11e4736da26fb785&autoload=false"></script>
        <script>
            kakao.maps.load(function() {{
                var container = document.getElementById('map');
                var options = {{
                    center: new kakao.maps.LatLng({USER_BASE_LAT}, {USER_BASE_LNG}),
                    level: 9
                }};
                var map = new kakao.maps.Map(container, options);
                
                // 마커 그리기
                {marker_js}
            }});
        </script>
    """
    
    # 3. 지도 렌더링
    st.components.v1.html(map_html, height=570)

st.markdown("---")
# 💡 개선 포인트 4: 데이터 동기화 버튼 클릭 시 캐시를 지우고 새로 불러오도록 변경
if st.button("🔄 로컬 마라톤 데이터베이스 강제 동기화 (70여 개 신규 데이터 포맷 빌드)"):
    st.cache_data.clear() # 기존에 캐싱된 데이터를 비웁니다.
    new_df = crawl_marathon_schedule()
    new_df.to_csv('data/marathons.csv', index=False)
    st.success("2026-2027 마스터 데이터 연동 성공!")
    st.rerun()