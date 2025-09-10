# 일본 여행 경비 추적기 Docker 컨테이너 설정
# Python 3.11 slim 이미지를 기본 이미지로 사용 (경량화된 버전)
FROM python:3.11-slim

# 컨테이너 내 작업 디렉토리를 /app으로 설정
WORKDIR /app

# Python 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 타임존 설정
ENV TZ=Asia/Seoul

# 시스템 의존성 패키지 설치
# gcc: SQLAlchemy 컴파일에 필요
# sqlite3: SQLite 데이터베이스 조작 도구
# curl: 헬스체크에 사용
# tzdata: 타임존 데이터
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        sqlite3 \
        curl \
        tzdata \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 의존성 파일을 먼저 복사 (Docker 레이어 캐싱 최적화)
COPY requirements.txt .

# pip 업그레이드 후 Python 패키지 설치
# --no-cache-dir: 캐시를 저장하지 않아 이미지 크기 최적화
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스코드를 컨테이너로 복사
# .dockerignore 파일에 의해 불필요한 파일은 제외됨
COPY . .

# Ensure static files directory exists and has proper permissions
RUN mkdir -p /app/static/css /app/static/js \
    && chmod -R 755 /app/static

# SQLite 데이터베이스 파일을 저장할 디렉토리 생성
# Docker 볼륨과 연결되어 데이터 영속성 보장
RUN mkdir -p /app/data

# 애플리케이션이 사용할 포트 8000번을 외부에 노출
EXPOSE 8000

# 컨테이너 헬스체크 설정
# 30초마다 /api/health 엔드포인트를 확인하여 서비스 상태 모니터링
# 3번 연속 실패시 unhealthy 상태로 판정
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 컨테이너 시작시 실행할 명령어
# uvicorn을 사용해 FastAPI 애플리케이션을 0.0.0.0:8000에서 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]