#!/usr/bin/env python3
"""
일본 여행 경비 더미 데이터 생성 스크립트
100개의 현실적인 지출 데이터를 생성합니다.
"""

import random
import sqlite3
from datetime import datetime, timedelta
import os

def create_dummy_data():
    """더미 데이터 100개 생성"""
    
    # 데이터베이스 연결
    db_path = "japan_travel_expenses.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 테이블이 없으면 생성 (기본 구조만)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_chat_id TEXT UNIQUE NOT NULL,
                email TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT,
                last_login TEXT,
                last_login_request TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT DEFAULT '',
                date TEXT NOT NULL,
                payment_method TEXT DEFAULT '현금',
                timestamp TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 기본 사용자 생성 (더미 데이터용)
        cursor.execute('SELECT id FROM users WHERE telegram_chat_id = ?', ("5469782369",))
        user = cursor.fetchone()
        
        if not user:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO users (telegram_chat_id, email, is_active, created_at, last_login) 
                VALUES (?, ?, ?, ?, ?)
            ''', ("5469782369", "dummy@test.com", 1, now_str, now_str))
            user_id = cursor.lastrowid
        else:
            user_id = user[0]
        
        # 일본 여행 기간 설정 (최근 2주간)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=14)
        
        # 카테고리별 데이터 설정
        categories = {
            "식비": {
                "descriptions": [
                    "라멘집", "스시 오마카세", "이자카야", "우동집", "카레전문점",
                    "가이센동", "야키니쿠", "텐푸라 정식", "편의점 도시락", "맥도날드",
                    "스타벅스", "카페", "타코야키", "오코노미야키", "크레페",
                    "빵집", "마트 과자", "길거리 음식", "패밀리레스토랑", "회전초밥"
                ],
                "amounts": range(1000, 50000, 500)
            },
            "교통비": {
                "descriptions": [
                    "JR 야마노테선", "도쿄메트로", "신칸센", "버스", "택시",
                    "공항리무진", "케이세이 스카이라이너", "JR패스", "도시바 일일권", "모노레일",
                    "지하철", "전철 한큐선", "한신전차", "오사카 지하철", "교토 버스"
                ],
                "amounts": range(200, 15000, 100)
            },
            "숙박비": {
                "descriptions": [
                    "비즈니스호텔", "료칸", "캡슐호텔", "게스트하우스", "에어비앤비",
                    "시티호텔", "온천 료칸", "망가카페", "사우나 숙박", "호스텔"
                ],
                "amounts": range(30000, 200000, 5000)
            },
            "입장료": {
                "descriptions": [
                    "디즈니랜드", "디즈니씨", "USJ", "스카이트리", "도쿄타워",
                    "후지큐 하이랜드", "오사카성", "금각사", "우에노 동물원", "아쿠아리움",
                    "미술관", "박물관", "온센", "가라오케", "게임센터",
                    "전망대", "신사 참배", "테마파크", "공원", "체험관"
                ],
                "amounts": range(500, 30000, 500)
            },
            "기타": {
                "descriptions": [
                    "기념품", "쇼핑", "약국", "의류", "화장품",
                    "전자제품", "만화책", "피규어", "문구용품", "잡화",
                    "선물", "과자선물", "술", "담배", "우산",
                    "충전기", "SIM카드", "WiFi렌탈", "세탁", "짐보관"
                ],
                "amounts": range(500, 80000, 500)
            }
        }
        
        # 결제수단 가중치 설정 (현실적인 비율)
        payment_methods_weights = [
            ("현금", 40),
            ("체크카드", 30),
            ("신용카드", 25),
            ("교통카드", 5)
        ]
        
        payment_methods = []
        for method, weight in payment_methods_weights:
            payment_methods.extend([method] * weight)
        
        print("더미 데이터 생성 시작...")
        
        # 100개 더미 데이터 생성
        for i in range(100):
            # 랜덤 카테고리 선택 (가중치 적용)
            category_weights = [
                ("식비", 40),
                ("교통비", 25),
                ("입장료", 15),
                ("숙박비", 10),
                ("기타", 10)
            ]
            
            category_list = []
            for cat, weight in category_weights:
                category_list.extend([cat] * weight)
            
            category = random.choice(category_list)
            
            # 해당 카테고리의 데이터 선택
            description = random.choice(categories[category]["descriptions"])
            amount = random.choice(categories[category]["amounts"])
            payment_method = random.choice(payment_methods)
            
            # 랜덤 날짜 생성 (여행 기간 내)
            random_days = random.randint(0, 14)
            expense_date = start_date + timedelta(days=random_days)
            
            # 시간도 랜덤하게 설정
            random_hour = random.randint(6, 23)
            random_minute = random.randint(0, 59)
            timestamp = datetime.combine(expense_date, datetime.min.time().replace(hour=random_hour, minute=random_minute))
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            # 데이터베이스에 삽입
            cursor.execute('''
                INSERT INTO expenses (user_id, amount, category, description, date, payment_method, timestamp) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, amount, category, description, expense_date.strftime("%Y-%m-%d"), payment_method, timestamp_str))
            
            if (i + 1) % 20 == 0:
                print(f"진행률: {i + 1}/100 ({(i + 1)}%)")
        
        # 데이터베이스에 저장
        conn.commit()
        print("✅ 더미 데이터 100개 생성 완료!")
        
        # 통계 출력
        print("\n📊 생성된 데이터 통계:")
        for category in categories.keys():
            cursor.execute('SELECT COUNT(*), SUM(amount) FROM expenses WHERE category = ?', (category,))
            result = cursor.fetchone()
            count = result[0] or 0
            total_amount = result[1] or 0
            print(f"  {category}: {count}건, 총 ₩{total_amount:,}")
        
        cursor.execute('SELECT COUNT(*), SUM(amount) FROM expenses')
        result = cursor.fetchone()
        total_expenses = result[0] or 0
        total_amount = result[1] or 0
        print(f"\n📈 전체: {total_expenses}건, 총 ₩{total_amount:,}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    create_dummy_data()