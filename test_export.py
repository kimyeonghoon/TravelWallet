#!/usr/bin/env python3
"""
데이터 내보내기 기능 테스트 스크립트
생성된 더미 데이터를 CSV/Excel 형태로 내보내기 테스트
"""

import sqlite3
import csv
import io
from datetime import datetime

def test_csv_export():
    """CSV 내보내기 기능 테스트"""
    print("📊 CSV 내보내기 기능 테스트 시작...")
    
    # 데이터베이스 연결
    conn = sqlite3.connect('japan_travel_expenses.db')
    cursor = conn.cursor()
    
    try:
        # 모든 지출 데이터 조회
        cursor.execute('''
            SELECT date, amount, category, description, payment_method, timestamp 
            FROM expenses 
            ORDER BY date DESC, timestamp DESC
        ''')
        
        expenses = cursor.fetchall()
        print(f"📋 총 {len(expenses)}건의 지출 데이터 발견")
        
        # 환율 설정 (테스트용)
        exchange_rate = 9.41
        
        # CSV 내용 생성
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 헤더 작성
        writer.writerow([
            "날짜", "금액(원)", "금액(엔)", "카테고리", "설명", "결제수단", "등록시간"
        ])
        
        total_amount = 0
        
        # 데이터 행 작성
        for expense in expenses:
            date, amount, category, description, payment_method, timestamp = expense
            jpy_amount = round(amount / exchange_rate)
            total_amount += amount
            
            writer.writerow([
                date,
                f"{amount:,.0f}",
                f"¥{jpy_amount:,}",
                category,
                description,
                payment_method,
                timestamp
            ])
        
        # 요약 행 추가
        total_jpy = round(total_amount / exchange_rate)
        writer.writerow([])
        writer.writerow([f"총 {len(expenses)}건", f"{total_amount:,.0f}원", f"¥{total_jpy:,}", "", "", "", ""])
        writer.writerow([f"환율 정보: 1엔 = {exchange_rate:.2f}원", "", "", "", "", "", ""])
        
        # CSV 파일로 저장
        csv_content = output.getvalue()
        output.close()
        
        filename = f"japan_expenses_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            f.write(csv_content)
        
        print(f"✅ CSV 파일 생성 완료: {filename}")
        print(f"💰 총 금액: ₩{total_amount:,} (¥{total_jpy:,})")
        
        # 첫 5줄 미리보기
        print(f"\n📄 CSV 파일 미리보기 (처음 5줄):")
        lines = csv_content.split('\n')
        for i, line in enumerate(lines[:7]):  # 헤더 + 5줄 + 빈줄
            if line.strip():
                print(f"  {i+1}: {line}")
        
        return filename
        
    except Exception as e:
        print(f"❌ CSV 생성 중 오류: {e}")
        return None
        
    finally:
        conn.close()

def test_category_filter():
    """카테고리별 필터링 테스트"""
    print("\n🔍 카테고리별 필터링 테스트...")
    
    conn = sqlite3.connect('japan_travel_expenses.db')
    cursor = conn.cursor()
    
    try:
        categories = ['식비', '교통비', '숙박비', '입장료', '기타']
        
        for category in categories:
            cursor.execute('SELECT COUNT(*), SUM(amount) FROM expenses WHERE category = ?', (category,))
            result = cursor.fetchone()
            count = result[0] or 0
            total = result[1] or 0
            
            if count > 0:
                print(f"  {category}: {count}건, ₩{total:,}")
                
                # 해당 카테고리 CSV 생성
                cursor.execute('''
                    SELECT date, amount, category, description, payment_method, timestamp 
                    FROM expenses 
                    WHERE category = ?
                    ORDER BY date DESC
                ''', (category,))
                
                expenses = cursor.fetchall()
                
                # 간단한 CSV 생성
                filename = f"test_{category}_{datetime.now().strftime('%H%M%S')}.csv"
                with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["날짜", "금액", "설명", "결제수단"])
                    
                    for expense in expenses:
                        writer.writerow([expense[0], f"₩{expense[1]:,}", expense[3], expense[4]])
                
                print(f"    → {filename} 생성됨")
        
    except Exception as e:
        print(f"❌ 필터링 테스트 중 오류: {e}")
        
    finally:
        conn.close()

def test_date_filter():
    """날짜별 필터링 테스트"""
    print("\n📅 날짜별 필터링 테스트...")
    
    conn = sqlite3.connect('japan_travel_expenses.db')
    cursor = conn.cursor()
    
    try:
        # 최근 7일 데이터
        from datetime import datetime, timedelta
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        cursor.execute('''
            SELECT COUNT(*), SUM(amount) 
            FROM expenses 
            WHERE date BETWEEN ? AND ?
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        result = cursor.fetchone()
        count = result[0] or 0
        total = result[1] or 0
        
        print(f"  최근 7일 ({start_date} ~ {end_date}): {count}건, ₩{total:,}")
        
        if count > 0:
            # 최근 7일 데이터 CSV 생성
            cursor.execute('''
                SELECT date, amount, category, description, payment_method 
                FROM expenses 
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC
            ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
            
            expenses = cursor.fetchall()
            
            filename = f"test_recent_7days_{datetime.now().strftime('%H%M%S')}.csv"
            with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["날짜", "금액", "카테고리", "설명", "결제수단"])
                
                for expense in expenses:
                    writer.writerow([expense[0], f"₩{expense[1]:,}", expense[2], expense[3], expense[4]])
            
            print(f"    → {filename} 생성됨")
        
    except Exception as e:
        print(f"❌ 날짜 필터링 테스트 중 오류: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧪 일본 여행 경비 내보내기 기능 테스트")
    print("=" * 50)
    
    # 전체 CSV 내보내기 테스트
    csv_file = test_csv_export()
    
    # 카테고리별 필터링 테스트
    test_category_filter()
    
    # 날짜별 필터링 테스트
    test_date_filter()
    
    print(f"\n🎉 테스트 완료! 생성된 파일들을 확인해보세요.")
    print(f"   주요 파일: {csv_file if csv_file else '생성 실패'}")