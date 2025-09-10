# 🚀 Nginx Reverse Proxy 배포 가이드

## 📋 개요

이 가이드는 nginx를 reverse proxy로 사용하여 Japan Travel Expense 애플리케이션을 배포하는 방법을 설명합니다.

## 🔧 해결된 Static 파일 문제

nginx reverse proxy 환경에서 static 파일을 제대로 서빙하기 위해 다음과 같은 개선사항을 적용했습니다:

### ✅ FastAPI 개선사항
1. **명시적 static 디렉토리 처리**: `os.path.join()`으로 절대 경로 사용
2. **CORS 미들웨어 추가**: nginx proxy 환경에서의 호환성 개선
3. **커스텀 static 파일 엔드포인트**: 적절한 MIME 타입과 캐시 헤더 설정
4. **Docker 내 static 파일 권한 설정**: 755 권한으로 파일 접근성 보장

## 🔄 배포 방법

### 방법 1: nginx에서 static 파일 직접 서빙 (권장)

**1. nginx 설정**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Static 파일은 nginx에서 직접 서빙 (성능상 이점)
    location /static/ {
        alias /path/to/your/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # API 요청은 FastAPI로 프록시
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**2. Docker Compose에서 static 디렉토리 볼륨 마운트**
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./static:/app/static:ro  # static 파일을 read-only로 마운트
```

### 방법 2: FastAPI에서 static 파일 서빙

nginx 설정에서 static 파일을 별도 처리하지 않고 모든 요청을 FastAPI로 전달:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🐳 Docker Compose 전체 설정

```yaml
version: '3.8'

services:
  # FastAPI 애플리케이션
  app:
    build: .
    container_name: japan-travel-expense
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./static:/app/static:ro
    environment:
      - PYTHONUNBUFFERED=1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: nginx-proxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./static:/var/www/static:ro  # nginx에서 직접 서빙할 static 파일
      - ./ssl:/etc/nginx/ssl:ro  # SSL 인증서 (선택사항)
    depends_on:
      - app
```

## 🔍 문제 해결

### Static 파일이 404 에러가 날 때

1. **컨테이너 내부 확인**:
```bash
docker exec -it japan-travel-expense ls -la /app/static/
```

2. **nginx 설정 테스트**:
```bash
docker exec -it nginx-proxy nginx -t
```

3. **로그 확인**:
```bash
# FastAPI 로그
docker logs japan-travel-expense

# nginx 로그
docker logs nginx-proxy
```

### CORS 에러가 발생할 때

FastAPI 애플리케이션에 CORS 미들웨어가 추가되어 있으니 nginx 설정에서 다음 헤더를 추가:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    
    # CORS 헤더 추가
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
    add_header Access-Control-Allow-Headers "Content-Type, Authorization";
}
```

## 📈 성능 최적화

1. **Static 파일 캐싱**:
```nginx
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

2. **gzip 압축**:
```nginx
gzip on;
gzip_types text/css application/javascript application/json;
```

3. **Connection Pooling**:
```nginx
upstream fastapi_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}
```

## 🔐 보안 설정

1. **HTTPS 리디렉션**:
```nginx
server {
    listen 80;
    return 301 https://$server_name$request_uri;
}
```

2. **보안 헤더**:
```nginx
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header X-XSS-Protection "1; mode=block";
```

## 🚀 배포 명령어

```bash
# 1. 이미지 빌드 및 실행
docker-compose up --build -d

# 2. 로그 확인
docker-compose logs -f

# 3. 상태 확인
docker-compose ps

# 4. 재배포 (변경사항 반영)
docker-compose down
docker-compose up --build -d
```