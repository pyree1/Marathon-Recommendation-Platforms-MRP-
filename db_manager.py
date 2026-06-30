import sqlite3

def init_db():
    """데이터베이스 및 테이블 초기화"""
    with sqlite3.connect('marathon.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS results 
                          (title TEXT PRIMARY KEY, analysis TEXT)''')
        conn.commit()

def save_analysis(title, analysis):
    """분석 결과 저장 (이미 존재하면 REPLACE)"""
    with sqlite3.connect('marathon.db') as conn:
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO results (title, analysis) VALUES (?, ?)", (title, analysis))
        conn.commit()

def get_analysis(title):
    """타이틀로 분석 결과 조회"""
    with sqlite3.connect('marathon.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT analysis FROM results WHERE title=?", (title,))
        result = cursor.fetchone()
        return result[0] if result else None