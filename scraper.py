import pandas as pd
import random
import re
import requests
from urllib.parse import quote
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────
# 🖼️ 포스터 이미지 수집 로직
# 1순위: 대회 공식 홈페이지(link)에 접속해서 og:image(실제 포스터)를 가져옵니다.
# 2순위: 접속 실패/og:image 없음 → 대회명이 적힌 테마 컬러 대체 포스터를 생성합니다.
#        (랜덤 무관 사진(picsum) 대신, 적어도 "이 대회"라는 걸 알 수 있는 이미지)
# ─────────────────────────────────────────────────────────────

_OG_IMAGE_CACHE = {}  # link -> 실제 og:image url (또는 None)

THEME_COLORS = {
    "펀런 앤 페스티벌!": ("F472B6", "FFFFFF"),
    "자연 속 야생 날것의 매력!": ("16A34A", "FFFFFF"),
    "클래식 도심 레이서!": ("2563EB", "FFFFFF"),
}

_OG_IMAGE_PATTERN = re.compile(
    r'<meta[^>]+(?:property|name)=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']'
    r'|<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image["\']',
    re.IGNORECASE,
)


def _fetch_og_image(url, timeout=4):
    """대회 공식 홈페이지의 <meta property="og:image"> 태그(=실제 포스터)를 가져옵니다."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; MarathonPosterBot/1.0)"}
        res = requests.get(url, headers=headers, timeout=timeout)
        if res.status_code != 200 or not res.text:
            return None
        match = _OG_IMAGE_PATTERN.search(res.text)
        if not match:
            return None
        img_url = match.group(1) or match.group(2)
        if not img_url:
            return None
        if img_url.startswith("//"):
            img_url = "https:" + img_url
        elif img_url.startswith("/"):
            from urllib.parse import urljoin
            img_url = urljoin(url, img_url)
        return img_url
    except Exception:
        # 접속 실패, 타임아웃, 차단(hotlink/방화벽) 등 → 그냥 대체 포스터로 넘어감
        return None


def _get_real_poster(link):
    """같은 홈페이지(link)는 한 번만 요청하도록 캐싱"""
    if link not in _OG_IMAGE_CACHE:
        _OG_IMAGE_CACHE[link] = _fetch_og_image(link)
    return _OG_IMAGE_CACHE[link]


def _generate_placeholder_poster(title, theme):
    """실제 포스터를 못 가져왔을 때, 대회명 + 테마색이 들어간 대체 이미지를 생성"""
    bg, fg = THEME_COLORS.get(theme, ("64748B", "FFFFFF"))
    short_title = title if len(title) <= 16 else title[:15] + "…"
    text = quote(short_title)
    return f"https://dummyimage.com/300x200/{bg}/{fg}.png&text={text}"


def get_poster_image(link, title, theme):
    real_poster = _get_real_poster(link)
    if real_poster:
        return real_poster
    return _generate_placeholder_poster(title, theme)


def crawl_marathon_schedule():
    """
    중복 없는 대한민국 주요 마라톤 대회 60개 마스터 데이터 생성기
    (실제 홈페이지 링크 및 다양한 조건 반영)
    """
    random.seed(42) 

    # 실제 마라톤 대회 기반의 고유한 데이터 셋
    base_marathons = [
        {"title": "서울 레이스", "location": "서울", "theme": "클래식 도심 레이서!", "link": "http://www.seoul-race.co.kr"},
        {"title": "동아마라톤 (서울국제마라톤)", "location": "서울", "theme": "클래식 도심 레이서!", "link": "http://www.seoul-marathon.com"},
        {"title": "JTBC 서울 마라톤", "location": "서울", "theme": "클래식 도심 레이서!", "link": "https://marathon.jtbc.com"},
        {"title": "춘천마라톤", "location": "강원", "theme": "클래식 도심 레이서!", "link": "http://marathon.chosun.com"},
        {"title": "경주국제마라톤", "location": "경북", "theme": "클래식 도심 레이서!", "link": "http://www.gyeongjumarathon.com"},
        {"title": "대구국제마라톤", "location": "대구", "theme": "클래식 도심 레이서!", "link": "https://daegumarathon.com"},
        {"title": "부산바다마라톤", "location": "부산", "theme": "클래식 도심 레이서!", "link": "http://www.marathon.busan.com"},
        {"title": "제주국제감귤마라톤", "location": "제주", "theme": "펀런 앤 페스티벌!", "link": "http://www.mandarinmarathon.com"},
        {"title": "경기평화마라톤", "location": "경기", "theme": "클래식 도심 레이서!", "link": "http://www.peacemarathon.co.kr"},
        {"title": "여의도 벚꽃 마라톤", "location": "서울", "theme": "펀런 앤 페스티벌!", "link": "http://www.cherryblossomrun.com"},
        {"title": "영남알프스 트레일런", "location": "울산", "theme": "자연 속 야생 날것의 매력!", "link": "http://www.ynalps.com"},
        {"title": "제주 트레일러닝", "location": "제주", "theme": "자연 속 야생 날것의 매력!", "link": "http://www.jejutrail.com"},
        {"title": "TNF 100 KOREA (강릉)", "location": "강원", "theme": "자연 속 야생 날것의 매력!", "link": "https://www.thenorthfacekorea.co.kr/tnf100"},
        {"title": "컬러런 코리아", "location": "서울", "theme": "펀런 앤 페스티벌!", "link": "http://www.thecolorrun.co.kr"},
        {"title": "좀비런 코리아", "location": "경기", "theme": "펀런 앤 페스티벌!", "link": "http://www.zombierun.co.kr"},
        {"title": "DMZ 평화 펀런", "location": "경기", "theme": "펀런 앤 페스티벌!", "link": "http://www.dmzrun.com"},
        {"title": "광주 5.18 민주항쟁 기념 마라톤", "location": "광주", "theme": "클래식 도심 레이서!", "link": "http://www.518marathon.com"},
        {"title": "대전맨몸마라톤", "location": "대전", "theme": "펀런 앤 페스티벌!", "link": "http://www.djrun.or.kr"},
        {"title": "세종호수공원 마라톤", "location": "세종", "theme": "클래식 도심 레이서!", "link": "http://www.sejongrun.com"},
        {"title": "천안 유관순 평화 마라톤", "location": "충남", "theme": "클래식 도심 레이서!", "link": "http://www.cheonanrun.com"},
        {"title": "청주 대청호 마라톤", "location": "충북", "theme": "자연 속 야생 날것의 매력!", "link": "http://www.cjrun.com"},
        {"title": "군산새만금국제마라톤", "location": "전북", "theme": "클래식 도심 레이서!", "link": "http://www.smgrun.com"},
        {"title": "순천만 에코 마라톤", "location": "전남", "theme": "자연 속 야생 날것의 매력!", "link": "http://www.eco-run.com"},
        {"title": "창원 통일 마라톤", "location": "경남", "theme": "클래식 도심 레이서!", "link": "http://www.cwrun.com"},
        {"title": "울산 태화강 마라톤", "location": "울산", "theme": "클래식 도심 레이서!", "link": "http://www.ulsanrun.com"},
        {"title": "인천 송도 하프 마라톤", "location": "인천", "theme": "클래식 도심 레이서!", "link": "http://www.songdorun.com"},
        {"title": "아식스 쿨 런", "location": "서울", "theme": "펀런 앤 페스티벌!", "link": "https://www.asics.com/kr/ko-kr/coolrun"},
        {"title": "나이키 위런 서울", "location": "서울", "theme": "펀런 앤 페스티벌!", "link": "https://www.nike.com/kr/ko_kr/c/runclub"},
        {"title": "뉴발란스 런온", "location": "서울", "theme": "펀런 앤 페스티벌!", "link": "https://www.nbkorea.com/runon"},
        {"title": "아디다스 마이런 부산", "location": "부산", "theme": "펀런 앤 페스티벌!", "link": "https://www.adidas.co.kr/mi-run"},
    ]

    # 부족한 데이터를 채우기 위한 확장(Variation) 로직 - 이름이 절대 겹치지 않게 연도와 수식어 부여
    prefixes = ["새봄맞이", "한여름밤의", "단풍", "눈꽃", "자선", "가족사랑", "해변", "산림욕", "역사탐방", "별빛"]
    
    while len(base_marathons) < 60:
        base = random.choice(base_marathons)
        prefix = random.choice(prefixes)
        # 예: 2026 단풍 대전맨몸마라톤 대회
        new_title = f"2026 {prefix} {base['title'].replace('2026', '').strip()} 대회"
        
        # 중복 체크
        if not any(m['title'] == new_title for m in base_marathons):
            base_marathons.append({
                "title": new_title,
                "location": base["location"],
                "theme": base["theme"],
                "link": base["link"] # 원래 홈페이지 링크 유지
            })

    # 위경도 매핑 (랜덤하게 분산)
    loc_coords = {
        "서울": (37.5665, 126.9780), "경기": (37.2636, 127.0286), "인천": (37.4563, 126.7052),
        "강원": (37.8813, 127.7298), "충남": (36.6588, 126.6728), "충북": (36.6356, 127.4913),
        "대전": (36.3504, 127.3845), "세종": (36.4800, 127.2890), "경북": (36.5760, 128.5056),
        "경남": (35.2383, 128.6925), "대구": (35.8714, 128.6014), "부산": (35.1796, 129.0756),
        "울산": (35.5396, 129.3115), "전북": (35.8242, 127.1480), "전남": (34.8161, 126.4629),
        "광주": (35.1595, 126.8526), "제주": (33.4890, 126.4983)
    }

    data = []
    start_date = datetime(2026, 7, 1) # 2026년 하반기 기준
    
    for i, m in enumerate(base_marathons):
        event_date = start_date + timedelta(days=random.randint(10, 180))
        reg_start = event_date - timedelta(days=random.randint(60, 90))
        reg_end = event_date - timedelta(days=random.randint(15, 30))
        
        # 상태 계산
        now = datetime.now()
        if now < reg_start: status = "접수예정"
        elif reg_start <= now <= reg_end: status = "접수중"
        else: status = "접수마감"

        scale = random.choice(["대규모 (1만명 이상)", "중규모 (3천명~1만명)", "소규모 (3천명 미만)"])
        style = random.choice(["초보 러너 (완주 목표)", "PB 도전 (기록 달성)"])
        
        course_opts = ["5K", "10K", "Half", "Full"]
        num_courses = random.randint(1, 4)
        course_list = random.sample(course_opts, num_courses)
        
        # 장거리 테마일 경우 특수 코스 추가
        if m["theme"] == "자연 속 야생 날것의 매력!":
            course_list.append("장거리 (60km 이상)")
            
        fee_num = random.choice([30000, 40000, 50000, 60000, 70000, 100000])

        base_lat, base_lng = loc_coords[m["location"]]
        
        data.append({
            "title": m["title"],
            "location": m["location"],
            "date": event_date.strftime("%Y-%m-%d"),
            "period": f"{reg_start.strftime('%Y.%m.%d')} - {reg_end.strftime('%Y.%m.%d')}",
            "status": status,
            "theme": m["theme"],
            "scale": scale,
            "style": style,
            "course": ", ".join(course_list),
            "fee": f"{fee_num:,}원",
            "fee_numeric": fee_num,
            "link": m["link"], # 개별 다이렉트 링크!
            "lat": base_lat + random.uniform(-0.1, 0.1),
            "lng": base_lng + random.uniform(-0.1, 0.1),
            "poster": get_poster_image(m["link"], m["title"], m["theme"])  # 실제 포스터(og:image) 우선, 실패 시 테마 대체 이미지
        })

    return pd.DataFrame(data)

if __name__ == "__main__":
    df = crawl_marathon_schedule()
    df.to_csv("marathons.csv", index=False)
    print("성공적으로 60개의 고유한 마라톤 데이터가 생성되었습니다.")