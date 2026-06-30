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

USER_BASE_LAT = 36.8143
USER_BASE_LNG = 127.1493
df['distance_km'] = df.apply(lambda r: calculate_distance(USER_BASE_LAT, USER_BASE_LNG, r['lat'], r['lng']), axis=1)

# 세션 상태 변수 초기화
if 'survey_active' not in st.session_state: st.session_state.survey_active = False
if 'survey_step' not in st.session_state: st.session_state.survey_step = 1
if 'show_popup' not in st.session_state: st.session_state.show_popup = False

# 퀴즈 상태 머신
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

@st.dialog("🎯 나만의 마라톤 핏(Fit) 찾기 초스피드 Quiz")
def show_survey_popup():
    step = st.session_state.survey_step
    
    st.progress(step / 5.0, text=f"**현재 {step}단계 진행 중 / 총 5단계**")
    st.markdown("---")
    
    if step == 1:
        st.markdown("#### **🎉 Q1. 어떤 테마/컨셉의 대회를 선호하시나요?**")
        st.session_state.tmp_concept = st.radio(
            "지루한 러닝은 거부한다! 당신의 취향은?", 
            [
                "🌍 상관없음 (전체 다 볼래요!)", 
                "🥳 펀런 앤 페스티벌! (무도런/나는솔로런 같은 이색 이벤트)", 
                "⛰️ 자연 속 야생 날것의 매력! (산악 트레일런)",
                "⏱️ 클래식 도심 레이서! (전통 시티/강변 코스)"
            ], 
            index=0
        )
        
    elif step == 2:
        st.markdown("#### **🏁 Q2. 이번에 목표로 하는 타겟 코스는 무엇인가요?**")
        st.session_state.tmp_distances = st.multiselect(
            "다중 선택 가능", 
            ["5K", "10K", "Half", "Full", "장거리 (60km 이상)"], 
            default=st.session_state.tmp_distances
        )
        
    elif step == 3:
        st.markdown("#### **👥 Q3. 대회장 인파 및 인프라 규모는 어느 정도가 좋으세요?**")
        st.session_state.tmp_scale = st.radio(
            "축제 규모 픽하기", 
            ["ALL (전체)", "대규모 (1만명 이상)", "중규모 (3천명~1만명)", "소규모 (3천명 미만)"], 
            index=0
        )
        
    elif step == 4:
        st.markdown("#### **⚡ Q4. 본인의 페이스 조절 및 난이도 성향은?**")
        st.session_state.tmp_style = st.radio(
            "러닝 스타일 결정", 
            ["ALL (전체)", "초보 러너 (완주 목표)", "PB 도전 (기록 달성)"], 
            index=0
        )
        
    elif step == 5:
        st.markdown("#### **💰 Q5. 지갑 사정을 고려한 참가비 상한선은?**")
        st.session_state.tmp_max_fee = st.slider(
            "최대 허용 참가비(원)", 
            30000, 150000, st.session_state.tmp_max_fee, 5000
        )

    st.markdown("<br>", unsafe_allow_html=True)
    
    b_col1, b_col2 = st.columns([1, 1])
    with b_col1:
        if step > 1:
            if st.button("⬅️ 이전 단계", use_container_width=True):
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

# 💡 개선 포인트 3: 버튼 텍스트 단순화 + 큰 사이즈 적용을 위한 키 컨테이너
with st.container(key="top_action_buttons"):
    c_pop1, c_pop2 = st.columns([2, 1])
    with c_pop1:
        if st.button("🎯 3초 만에 나만의 맞춤 대회 찾기", type="primary", use_container_width=True):
            st.session_state.survey_step = 1
            st.session_state.show_popup = True
            st.rerun()
    with c_pop2:
        if st.button("🌐 조건 해제 (전체 대회 보기)", use_container_width=True):
            st.session_state.survey_active = False
            st.rerun()

if st.session_state.show_popup:
    show_survey_popup()

# ─── 🔍 사이드바 기본 행정망 필터 ───
st.sidebar.header("🔍 상세 행정망 필터")
with st.sidebar.form(key='sidebar_search_trigger'):
    selected_region = st.selectbox("📍 개최 권역", options=["전체"] + sorted(df['location'].unique().tolist()))
    selected_status = st.selectbox("🚦 모집 진행 상황", options=["전체"] + sorted(df['status'].unique().tolist()))
    max_dist_filter = st.slider("🚗 내 거점(천안) 기준 반경 (km)", 10, 300, 200, 10)
    submit_sidebar = st.form_submit_button(label="🔍 조건 반영하여 검색하기", use_container_width=True)

# 데이터 필터링 파이프라인
filtered_df = df.copy()

if selected_region != "전체": filtered_df = filtered_df[filtered_df['location'] == selected_region]
if selected_status != "전체": filtered_df = filtered_df[filtered_df['status'] == selected_status]
filtered_df = filtered_df[filtered_df['distance_km'] <= max_dist_filter]

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
    
    if filtered_df.empty:
        st.warning("앗! 조건에 딱 들어맞는 대회가 아쉽게도 없습니다. 팝업 설문을 다시 실행해 범위를 넓혀보세요!")
    else:
        with st.container(height=650):
            for _, row in filtered_df.iterrows():
                with st.container(border=True):
                    card_img, card_left, card_right = st.columns([0.8, 2.1, 1.1])
                    
                    with card_img:
                        # 💡 이미지 포스터가 없을 때를 대비한 꼼꼼한 체크
                        poster_url = row['poster'] if pd.notnull(row['poster']) else "https://via.placeholder.com/300x200"
                        st.image(poster_url, use_container_width=True)
                    
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
    
    marker_js = ""
    for _, row in filtered_df.iterrows():
        if 'lat' in row and 'lng' in row:
            if not pd.isna(row['lat']) and not pd.isna(row['lng']):
                marker_js += f"""
                    var markerPos = new kakao.maps.LatLng({row['lat']}, {row['lng']});
                    var marker = new kakao.maps.Marker({{
                        position: markerPos,
                        clickable: true
                    }});
                    marker.setMap(map);
                    
                    var iwContent = '<div style="padding:10px;font-size:12px;color:#000;width:220px;font-family:sans-serif;"><b>{row['title']}</b><br><span style="color:#666;">{row['theme']}</span></div>';
                    var infowindow = new kakao.maps.InfoWindow({{ content: iwContent }});
                    
                    kakao.maps.event.addListener(marker, 'click', (function(m, info) {{
                        return function() {{
                            if (activeInfoWindow) {{ activeInfoWindow.close(); }}
                            info.open(map, m);
                            activeInfoWindow = info;
                        }};
                    }})(marker, infowindow));
                """

    map_html = f"""
        <div id="map" style="width:100%;height:530px;border-radius:12px;box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);"></div>
        <script type="text/javascript" src="//dapi.kakao.com/v2/maps/sdk.js?appkey=e265c9f38550c96c11e4736da26fb785"></script>
        <script>
            var activeInfoWindow = null;
            setTimeout(function() {{
                var container = document.getElementById('map');
                var options = {{
                    center: new kakao.maps.LatLng({USER_BASE_LAT}, {USER_BASE_LNG}),
                    level: 11
                }};
                var map = new kakao.maps.Map(container, options);
                
                if (navigator.geolocation) {{
                    navigator.geolocation.getCurrentPosition(function(position) {{
                        var lat = position.coords.latitude;
                        var lon = position.coords.longitude;
                        var locPosition = new kakao.maps.LatLng(lat, lon);
                        
                        var markerImage = new kakao.maps.MarkerImage(
                            'https://t1.daumcdn.net/localimg/localimages/07/2018/pc/img/marker_spot.png',
                            new kakao.maps.Size(24, 35)
                        );
                        var locMarker = new kakao.maps.Marker({{
                            map: map,
                            position: locPosition,
                            image: markerImage
                        }});
                        
                        var customOverlay = new kakao.maps.CustomOverlay({{
                            position: locPosition,
                            content: '<div style="background-color:#2563EB; color:white; padding:3px 8px; border-radius:10px; font-size:10px; font-weight:bold; box-shadow:0 2px 4px rgba(0,0,0,0.2);">내 위치</div>',
                            yAnchor: 2.5
                        }});
                        customOverlay.setMap(map);
                    }});
                }}
                {marker_js}
            }}, 400);
        </script>
    """
    st.components.v1.html(map_html, height=550)

st.markdown("---")
# 💡 개선 포인트 4: 데이터 동기화 버튼 클릭 시 캐시를 지우고 새로 불러오도록 변경
if st.button("🔄 로컬 마라톤 데이터베이스 강제 동기화 (70여 개 신규 데이터 포맷 빌드)"):
    st.cache_data.clear() # 기존에 캐싱된 데이터를 비웁니다.
    new_df = crawl_marathon_schedule()
    new_df.to_csv('data/marathons.csv', index=False)
    st.success("2026-2027 마스터 데이터 연동 성공!")
    st.rerun()