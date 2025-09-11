"""
환율 서비스

이 파일은 한국수출입은행 공식 환율 API를 사용하여 실시간 JPY-KRW 환율을 제공합니다.
API 호출 최적화를 위한 캐싱 기능과 API 장애 시 폴백 처리를 포함합니다.

주요 기능:
- 한국수출입은행 공식 환율 API 연동
- 5분간 환율 데이터 캐싱으로 API 호출 최적화
- API 장애 시 기본 환율(9.5원) 제공
- 일본 엔화(JPY) → 한국 원화(KRW) 환율 전문 처리

API 정보:
- 제공: 한국수출입은행 (Korea Export-Import Bank)
- 갱신 주기: 영업일 기준 실시간
- 기본 환율: 1엔 = 9.5원 (API 장애 시)
"""

# 외부 라이브러리 임포트
import requests  # HTTP API 호출
import os  # 환경변수 접근
from datetime import datetime  # 캐시 타임스탬프 관리
from typing import Dict, Optional  # 타입 힌팅
import logging  # 로깅

# 로거 설정
logger = logging.getLogger(__name__)

class ExchangeRateService:
    """
    환율 정보 제공 서비스
    한국수출입은행 API를 통해 실시간 JPY-KRW 환율을 제공하며,
    캐싱과 폴백 처리로 안정적인 서비스를 보장합니다.
    """
    
    def __init__(self):
        """환율 서비스 초기화"""
        self.api_key = os.getenv("KOREA_EXIM_KEY")  # 한국수출입은행 API 키
        self.base_url = "https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"  # API 엔드포인트
        self.cache = {}  # 환율 데이터 캐시
        self.cache_timestamp = None  # 캐시 타임스탬프
        
    def get_exchange_rates(self, search_date: Optional[str] = None) -> Dict:
        """
        한국수출입은행 환율 API에서 환율 정보를 가져옵니다.
        
        Args:
            search_date: YYYYMMDD 형식의 날짜 (선택사항)
            
        Returns:
            Dict: 환율 정보 딕셔너리
        """
        if not self.api_key:
            logger.error("KOREA_EXIM_KEY not found in environment variables")
            return self._get_fallback_rate()
            
        # 캐시 확인 (5분간 유효)
        now = datetime.now()
        if (self.cache_timestamp and 
            (now - self.cache_timestamp).seconds < 300 and
            self.cache):
            logger.info("Using cached exchange rate data")
            return self.cache
            
        params = {
            "authkey": self.api_key,
            "data": "AP01"
        }
        
        if search_date:
            params["searchdate"] = search_date
            
        try:
            response = requests.get(self.base_url, params=params, timeout=10, verify='/etc/ssl/certs/ca-bundle.crt')
            response.raise_for_status()
            
            rates_data = response.json()
            
            # 응답을 딕셔너리로 변환
            rates_dict = {}
            for rate in rates_data:
                if rate.get("result") == 1:  # 성공적인 데이터만
                    currency_code = rate["cur_unit"]
                    rates_dict[currency_code] = {
                        "currency_name": rate["cur_nm"],
                        "basic_rate": self._parse_rate(rate["deal_bas_r"]),
                        "buy_rate": self._parse_rate(rate["ttb"]),
                        "sell_rate": self._parse_rate(rate["tts"]),
                        "raw_data": rate
                    }
            
            # 캐시 업데이트
            self.cache = rates_dict
            self.cache_timestamp = now
            
            logger.info(f"Successfully fetched {len(rates_dict)} exchange rates")
            return rates_dict
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return self._get_fallback_rate()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return self._get_fallback_rate()
    
    def get_jpy_to_krw_rate(self) -> float:
        """
        일본 엔화(JPY) -> 한국 원화(KRW) 환율을 가져옵니다.
        
        Returns:
            float: 1엔당 원화 환율 (100엔 기준을 1엔으로 변환)
        """
        rates = self.get_exchange_rates()
        
        if "JPY(100)" in rates:
            # 100엔 기준 환율을 1엔 기준으로 변환
            return rates["JPY(100)"]["basic_rate"] / 100
        
        # 폴백 환율 (최근 평균값)
        logger.warning("JPY rate not found, using fallback rate")
        return 9.5
    
    def convert_jpy_to_krw(self, jpy_amount: float) -> int:
        """
        엔화 금액을 원화로 변환합니다.
        
        Args:
            jpy_amount: 엔화 금액
            
        Returns:
            int: 변환된 원화 금액 (반올림)
        """
        rate = self.get_jpy_to_krw_rate()
        return round(jpy_amount * rate)
    
    def convert_krw_to_jpy(self, krw_amount: float) -> int:
        """
        원화 금액을 엔화로 변환합니다.
        
        Args:
            krw_amount: 원화 금액
            
        Returns:
            int: 변환된 엔화 금액 (반올림)
        """
        rate = self.get_jpy_to_krw_rate()
        return round(krw_amount / rate)
    
    def _parse_rate(self, rate_str: str) -> float:
        """
        쉼표가 포함된 환율 문자열을 float으로 변환합니다.
        
        Args:
            rate_str: "1,234.56" 형태의 환율 문자열
            
        Returns:
            float: 변환된 환율
        """
        try:
            return float(rate_str.replace(",", ""))
        except (ValueError, AttributeError):
            return 0.0
    
    def _get_fallback_rate(self) -> Dict:
        """
        API 호출 실패 시 사용할 폴백 환율 데이터를 반환합니다.
        
        Returns:
            Dict: 기본 환율 데이터
        """
        logger.warning("Using fallback exchange rate data")
        return {
            "JPY(100)": {
                "currency_name": "일본 옌",
                "basic_rate": 950.0,  # 100엔 = 950원 (임시값)
                "buy_rate": 931.0,
                "sell_rate": 969.0,
                "raw_data": None
            }
        }
    
    def get_rate_info(self) -> Dict:
        """
        환율 정보와 메타데이터를 반환합니다.
        
        Returns:
            Dict: 환율 정보 및 메타데이터
        """
        jpy_rate = self.get_jpy_to_krw_rate()
        
        return {
            "jpy_to_krw_rate": jpy_rate,
            "rate_per_100_jpy": jpy_rate * 100,
            "last_updated": self.cache_timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.cache_timestamp else "알 수 없음",
            "data_source": "한국수출입은행"
        }

# 전역 인스턴스
exchange_service = ExchangeRateService()