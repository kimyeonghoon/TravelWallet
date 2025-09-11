# 🇯🇵 일본 여행 경비 추적 시스템

일본 여행 중 발생하는 모든 경비를 체계적으로 관리하고 추적할 수 있는 웹 애플리케이션입니다.

## ✨ 주요 기능

### 💰 지출 관리
- **지출 추가**: 금액, 카테고리, 설명, 결제 수단, 날짜 입력
- **지출 수정**: 모든 필드 수정 가능 (Bootstrap 모달 사용)
- **지출 삭제**: 확인 후 영구 삭제
- **실시간 요약**: 총 지출, 오늘 지출 통계

### 🏷️ 카테고리 시스템
- **식비**: 식당, 카페, 간식 등
- **교통비**: 지하철, 버스, 택시, 전철 등  
- **숙박비**: 호텔, 료칸, 게스트하우스 등
- **입장료**: 관광지, 박물관, 테마파크 등
- **기타**: 쇼핑, 선물, 기타 잡비 등

### 💳 결제 수단 시스템
- **현금**: 일본 엔화 현금 지불
- **체크카드**: 국내/해외 직불카드 사용
- **신용카드**: 신용카드 결제
- **교통카드**: IC카드(스이카, 파스모 등) 사용

### 🔐 인증 시스템
- **이메일 기반 텔레그램 인증**: 사전 등록된 이메일로 텔레그램 봇 코드 발송
- **IP 기반 Rate Limiting**: 5회 실패 시 10분간 자동 차단
- **간편 로그인 모달**: 별도 페이지 없이 메인 페이지 내 모달 로그인
- **JWT 토큰**: 15분 만료 세션 토큰으로 보안 강화
- **권한별 기능 제어**: 로그인 사용자만 지출 추가/수정/삭제 가능

### 💱 환율 시스템
- **실시간 환율 연동**: 한국수출입은행 공식 API를 통한 정확한 환율 정보
- **스마트 캐싱**: 5분간 환율 데이터 캐시로 API 호출 최적화
- **홈페이지 환율 표시**: 현재 JPY-KRW 환율을 카드 형태로 명확히 표시
- **교통카드 환율 표시**: ¥1,000 = ₩9,409 형태로 직관적 환율 표시
- **통화 토글 입력**: 지출 추가 시 ₩/¥ 버튼으로 간편한 통화 선택
- **자동 환율 변환**: 엔화 입력 시 실시간 원화 환산 및 자동 저장
- **폴백 처리**: API 장애 시 기본 환율(9.5원/엔)로 서비스 지속

### 🎯 교통카드 관리
- **교통카드 추가**: 스이카, 파스모 등 IC카드 등록
- **잔액 관리**: 각 카드별 잔액 추적 및 수정
- **총 잔액 표시**: 모든 교통카드 잔액 합계 (엔화 → 원화 환산)
- **실시간 환율 적용**: 홈페이지에서 원화 환산 잔액 확인

### 💼 엔화지갑 관리
- **지갑 추가**: 여러 개의 엔화 지갑 관리 (메인지갑, 여권지갑 등)
- **잔액 추적**: 각 지갑별 엔화 잔액 관리
- **현금 지출 연동**: 현금 결제 시 특정 지갑 선택 가능
- **총 잔액 표시**: 모든 지갑 잔액 합계 (엔화 → 원화 환산)

### 📊 통계 및 시각화
- **고급 차트 대시보드**: Chart.js 기반 인터랙티브 차트
- **카테고리별 지출 차트**: 파이 차트로 비율 시각화
- **결제수단별 지출 차트**: 도넛 차트로 분석
- **일별 지출 추이**: 라인 차트로 시계열 분석
- **요일별 지출 패턴**: 바 차트로 요일별 소비 분석
- **최대 지출 TOP 5**: 큰 지출 내역 하이라이트
- **실시간 통계**: 총 지출, 건수, 일평균, 지출일수
- **데이터 내보내기**: CSV/Excel 파일로 필터링 내보내기

### 📱 사용자 경험
- **반응형 디자인**: 모바일/태블릿/데스크톱 지원
- **직관적 UI**: Bootstrap 5 기반 깔끔한 인터페이스
- **공개 지출 조회**: 누구나 지출 내역과 통계 확인 가능
- **권한별 UI**: 로그인 상태에 따른 기능 표시/숨김
- **실시간 알림**: 성공/오류 메시지 표시
- **한국어 지원**: 완전한 한국어 인터페이스
- **자동 세션 관리**: 만료된 세션 자동 감지 및 재로그인 유도

## 🛠️ 기술 스택

### Backend
- **FastAPI**: Python 기반 고성능 웹 프레임워크
- **SQLAlchemy**: ORM (Object-Relational Mapping)
- **SQLite**: 경량 데이터베이스
- **JWT**: JSON Web Token 인증
- **Pydantic**: 데이터 검증

### Frontend
- **HTML5 + CSS3**: 시맨틱 마크업
- **Bootstrap 5**: 반응형 UI 프레임워크
- **jQuery**: DOM 조작 및 AJAX
- **Chart.js**: 인터랙티브 차트 라이브러리
- **Font Awesome**: 아이콘 라이브러리

### External APIs
- **한국수출입은행 환율 API**: 실시간 JPY-KRW 환율
- **텔레그램 Bot API**: 2FA 인증 코드 발송

### Deployment
- **Docker**: 컨테이너화 배포
- **Docker Compose**: 멀티 컨테이너 오케스트레이션
- **Nginx**: 리버스 프록시 (선택사항)

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/kimyeonghoon/JAPAN_TRAVEL_EXPENSE.git
cd JAPAN_TRAVEL_EXPENSE
```

### 2. 환경 설정
```bash
# 환경변수 파일 복사
cp .env.example .env

# .env 파일 편집 (필수 항목)
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
TELEGRAM_CHAT_ID=your-telegram-chat-id
ALLOWED_EMAIL=your-allowed-email@domain.com
SECRET_KEY=your-super-secret-jwt-key-min-32chars
KOREA_EXIM_KEY=your-korea-exim-api-key
```

### 3. Docker로 실행 (권장)
```bash
# 이미지 빌드 후 실행
docker-compose up --build

# 백그라운드에서 실행
docker-compose up -d

# 서비스 중지
docker-compose down
```

### 4. 로컬 개발 환경
```bash
# Python 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
python main.py
# 또는
uvicorn main:app --reload
```

### 5. 접속
- **메인 페이지**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **통계 페이지**: http://localhost:8000/statistics
- **교통카드 관리**: http://localhost:8000/transport-cards
- **엔화지갑 관리**: http://localhost:8000/wallets

## 🔧 환경 변수 설정

### 필수 설정
```env
# 텔레그램 봇 설정 (인증용)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-from-botfather
TELEGRAM_CHAT_ID=your-telegram-chat-id

# 인증 설정
ALLOWED_EMAIL=your-allowed-email@domain.com
SECRET_KEY=your-super-secret-jwt-key-min-32chars

# 환율 API 키
KOREA_EXIM_KEY=your-korea-exim-api-key
```

### 선택 설정
```env
# 보안 설정
MAX_LOGIN_ATTEMPTS=5
BAN_DURATION_MINUTES=10
ACCESS_TOKEN_EXPIRE_MINUTES=15

# 애플리케이션 설정
APP_URL=http://localhost:8000
```

## 📁 프로젝트 구조

```
JAPAN_TRAVEL_EXPENSE/
├── main.py                 # FastAPI 메인 애플리케이션
├── models.py              # SQLAlchemy 데이터베이스 모델
├── database.py            # 데이터베이스 서비스 레이어
├── auth.py                # 인증 및 보안 서비스
├── exchange_service.py    # 환율 서비스
├── requirements.txt       # Python 의존성
├── Dockerfile            # Docker 컨테이너 설정
├── docker-compose.yml    # Docker Compose 설정
├── .env.example          # 환경변수 템플릿
├── .gitignore           # Git 무시 파일 목록
├── templates/           # HTML 템플릿
│   ├── index.html       # 메인 페이지
│   ├── statistics.html  # 통계 페이지
│   ├── transport-cards.html # 교통카드 관리
│   └── wallets.html     # 엔화지갑 관리
├── static/              # 정적 파일
│   ├── css/            # 스타일시트
│   └── js/             # JavaScript
│       └── app.js      # 메인 애플리케이션 로직
└── data/               # 데이터베이스 파일 (Docker 볼륨)
    └── japan_travel_expenses.db
```

## 🔒 보안 기능

### 인증 시스템
- **이메일 사전 승인**: ALLOWED_EMAIL에 등록된 이메일만 로그인 가능
- **텔레그램 2FA**: 이메일 입력 후 텔레그램으로 6자리 코드 발송
- **JWT 토큰**: 15분 만료로 세션 보안 강화
- **IP 기반 Rate Limiting**: 5회 로그인 실패 시 10분간 IP 차단

### 데이터 보호
- **환경변수 분리**: 민감한 정보를 .env 파일로 분리
- **CORS 설정**: 허용된 오리진만 API 접근 가능
- **입력 검증**: Pydantic을 통한 강력한 데이터 검증

## 📊 API 문서

애플리케이션 실행 후 http://localhost:8000/docs 에서 자동 생성된 API 문서를 확인할 수 있습니다.

### 주요 엔드포인트

#### 인증
- `POST /api/request-login` - 로그인 코드 요청
- `POST /api/verify-login` - 로그인 코드 검증

#### 지출 관리
- `GET /api/expenses` - 지출 목록 조회
- `POST /api/expenses` - 지출 추가
- `PUT /api/expenses/{id}` - 지출 수정
- `DELETE /api/expenses/{id}` - 지출 삭제

#### 교통카드
- `GET /api/transport-cards` - 교통카드 목록
- `POST /api/transport-cards` - 교통카드 추가
- `PUT /api/transport-cards/{id}` - 교통카드 수정

#### 엔화지갑
- `GET /api/wallets` - 지갑 목록
- `POST /api/wallets` - 지갑 추가
- `PUT /api/wallets/{id}` - 지갑 수정

#### 기타
- `GET /api/exchange-rate` - 실시간 환율 조회
- `GET /api/summary` - 지출 요약 통계

## 🐳 Docker 배포

### 운영 환경 배포
```bash
# 프로덕션 빌드 및 실행
docker-compose -f docker-compose.yml up -d --build

# 로그 확인
docker-compose logs -f

# 컨테이너 상태 확인
docker-compose ps
```

### 헬스체크
```bash
# API 헬스체크
curl http://localhost:8000/api/health

# 컨테이너 헬스체크 상태
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## 📈 사용법

### 1. 초기 설정
1. 텔레그램 봇 생성 및 토큰 발급
2. .env 파일에 설정 정보 입력
3. Docker Compose로 애플리케이션 실행

### 2. 인증
1. 메인 페이지에서 "로그인" 버튼 클릭
2. 등록된 이메일 주소 입력
3. 텔레그램으로 받은 6자리 코드 입력

### 3. 지출 관리
1. 로그인 후 지출 추가 폼에서 정보 입력
2. 카테고리, 금액, 결제수단 선택
3. 현금 결제 시 지갑 선택 (선택사항)

### 4. 잔액 관리
1. 교통카드 페이지에서 IC카드 등록 및 잔액 관리
2. 엔화지갑 페이지에서 현금 지갑 관리
3. 홈페이지에서 총 잔액 확인

### 5. 통계 확인
1. 통계 페이지에서 다양한 차트 확인
2. 필터링 및 정렬 기능 활용
3. CSV/Excel 형태로 데이터 내보내기

## 🤝 기여하기

1. 저장소 Fork
2. 기능 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원

문제가 발생하거나 질문이 있으시면:
- 이슈 생성: [GitHub Issues](https://github.com/kimyeonghoon/JAPAN_TRAVEL_EXPENSE/issues)
- 이메일: me@yeonghoon.kim

## 🙏 감사의 말

- **한국수출입은행**: 환율 API 제공
- **Bootstrap**: 반응형 UI 프레임워크
- **Chart.js**: 데이터 시각화 라이브러리
- **FastAPI**: 고성능 웹 프레임워크
- **Claude Code**: 개발 지원

---

**Made with ❤️ for Japanese travelers**

🤖 Generated with [Claude Code](https://claude.ai/code)