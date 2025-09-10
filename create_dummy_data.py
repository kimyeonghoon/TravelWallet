#!/usr/bin/env python3
"""
더미 데이터 생성 스크립트
일본 여행 경비 추적기용 테스트 데이터를 생성합니다.
"""

import os
import sys
import random
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

# Add current directory to path to import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import create_tables, get_db, Expense, User
from auth import AuthService

# 더미 데이터 설정
CATEGORIES = ['food', 'transport', 'accommodation', 'admission', 'other']
PAYMENT_METHODS = ['현금', '체크카드', '신용카드', '교통카드']

# 카테고리별 더미 설명
DESCRIPTIONS = {
    'food': [
        '라멘 맛집에서 점심',
        '회전초밥 저녁식사', 
        '편의점 간식',
        '카페에서 커피',
        '이자카야에서 맥주',
        '규카츠 전문점',
        '오코노미야키',
        '타코야키 포장마차',
        '스시 오마카세',
        '모츠나베 저녁'
    ],
    'transport': [
        'JR 야마노테선',
        '지하철 이용료',
        '택시 요금',
        '신칸센 도쿄-오사카',
        '버스 요금',
        '공항 리무진',
        'IC카드 충전',
        '전철 일일권',
        '케이블카 요금',
        '렌터카 연료비'
    ],
    'accommodation': [
        '시부야 호텔 1박',
        '료칸 숙박비',
        '캡슐호텔',
        '게스트하우스',
        '비즈니스호텔',
        '온천료칸 2박',
        'Airbnb 숙박',
        '유스호스텔',
        '러브호텔',
        '망가카페 숙박'
    ],
    'admission': [
        '도쿄타워 입장료',
        '후지큐 하이랜드',
        '우에노 동물원',
        '센소지 절 관람',
        '오사카성 입장',
        '유니버설 스튜디오',
        '디즈니랜드 티켓',
        '메이지신궁 참배',
        '온천 입욕료',
        '스카이트리 전망대'
    ],
    'other': [
        '기념품 쇼핑',
        '약국에서 구매',
        '100엔샵 쇼핑',
        '만화책 구입',
        '일본 화장품',
        '전자제품 구매',
        '옷 쇼핑',
        '우산 구입',
        '휴대폰 충전기',
        '선물용 과자'
    ]
}

# 카테고리별 금액 범위 (엔화)
AMOUNT_RANGES = {
    'food': (500, 8000),
    'transport': (200, 15000), 
    'accommodation': (3000, 25000),
    'admission': (1000, 12000),
    'other': (300, 20000)
}

def create_dummy_data():
    """더미 데이터 생성"""
    print("일본 여행 경비 더미 데이터 생성 시작...")
    
    # 데이터베이스 테이블 생성
    create_tables()
    
    # 데이터베이스 세션 생성
    db = next(get_db())
    
    try:
        # 기본 사용자 생성 (이미 있으면 가져오기)
        user = AuthService.create_user(db, "5496782369")
        print(f"사용자 생성/확인 완료: Chat ID {user.telegram_chat_id}")
        
        # 기존 지출 데이터 확인
        existing_count = db.query(Expense).count()
        print(f"기존 지출 데이터: {existing_count}개")
        
        # 더미 데이터 생성 (최근 30일 범위)
        today = date.today()
        start_date = today - timedelta(days=30)
        
        expenses_created = 0
        
        for i in range(20):
            # 랜덤 카테고리 선택
            category = random.choice(CATEGORIES)
            
            # 카테고리에 맞는 금액 범위에서 선택
            min_amount, max_amount = AMOUNT_RANGES[category]
            amount = random.randint(min_amount, max_amount)
            
            # 랜덤 날짜 선택 (최근 30일)
            random_days = random.randint(0, 30)
            expense_date = start_date + timedelta(days=random_days)
            
            # 랜덤 시간 생성
            random_hours = random.randint(6, 23)
            random_minutes = random.randint(0, 59)
            timestamp = datetime.combine(expense_date, datetime.min.time().replace(
                hour=random_hours, minute=random_minutes
            ))
            
            # 랜덤 설명 선택
            description = random.choice(DESCRIPTIONS[category])
            
            # 랜덤 결제수단 선택
            payment_method = random.choice(PAYMENT_METHODS)
            
            # 지출 데이터 생성
            expense = Expense(
                user_id=user.id,
                amount=float(amount),
                category=category,
                description=description,
                date=expense_date.strftime("%Y-%m-%d"),
                payment_method=payment_method,
                timestamp=timestamp
            )
            
            db.add(expense)
            expenses_created += 1
            
            print(f"[OK] {expenses_created:2d}/20: {expense_date.strftime('%m/%d')} | "
                  f"{category:13s} | YEN{amount:6,d} | {payment_method:4s} | {description}")
        
        # 데이터베이스에 커밋
        db.commit()
        
        # 결과 요약
        total_count = db.query(Expense).count()
        total_amount = sum(e.amount for e in db.query(Expense).all())
        
        print(f"\n[완료] 더미 데이터 생성 완료!")
        print(f"[생성] 생성된 지출: {expenses_created}개")
        print(f"[통계] 총 지출 데이터: {total_count}개")
        print(f"[금액] 총 지출 금액: YEN{total_amount:,.0f}")
        
        # 카테고리별 통계
        print(f"\n[분류] 카테고리별 생성 현황:")
        for category in CATEGORIES:
            count = db.query(Expense).filter(Expense.category == category).count()
            category_names = {
                'food': '식비',
                'transport': '교통비', 
                'accommodation': '숙박비',
                'admission': '입장료',
                'other': '기타'
            }
            print(f"   {category_names[category]:5s}: {count:2d}개")
            
    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_dummy_data()