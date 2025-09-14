# 📋 요구사항 관리 (Requirements Management)

> 이 파일은 개발 중인 요구사항을 임시로 관리하는 파일입니다.  
> 완료된 요구사항은 CLAUDE.md에 반영 후 이 파일에서 삭제됩니다.

## 📌 현재 요구사항 (Current Requirements)

### 🔥 높은 우선순위 (High Priority)
<!-- 긴급하게 처리해야 할 요구사항들 -->
-웹앱을 안드로이드 APK로 변환 (하이브리드 앱)


### 📋 보통 우선순위 (Medium Priority)
<!-- 일반적인 기능 개선 및 추가 요구사항들 -->

### 💡 낮은 우선순위 (Low Priority)
<!-- 나중에 고려해볼 수 있는 요구사항들 -->
-PWA (Progressive Web App) 기능 추가
-오프라인 모드 지원
-푸시 알림 기능
-앱스토어 배포 준비
-네이티브 앱 기능 추가 (카메라, 파일 접근 등)

---

## 📋 안드로이드 APK 변환 가이드

### 🎯 목표
현재 웹앱을 안드로이드 APK로 변환하여 Play Store에 배포 가능한 하이브리드 앱 만들기

### 📝 준비사항
1. **Node.js 설치** (v16 이상)
2. **Android Studio 설치**
3. **Java Development Kit (JDK) 설치**
4. **현재 웹앱 백엔드 서버 배포** (클라우드/VPS)

### 🚀 단계별 진행 계획

#### Phase 1: Capacitor 하이브리드 앱 (1-2일)
1. **프로젝트 초기화**
   ```bash
   npm init -y
   npm install @capacitor/core @capacitor/cli
   npx cap init "Japan Travel Expense" "com.travel.expense"
   ```

2. **안드로이드 플랫폼 추가**
   ```bash
   npm install @capacitor/android
   npx cap add android
   ```

3. **웹 리소스 준비**
   - 현재 static 폴더 구조 유지
   - index.html을 진입점으로 설정
   - API 엔드포인트를 배포된 서버로 변경

4. **빌드 및 테스트**
   ```bash
   npx cap sync
   npx cap open android
   ```

#### Phase 2: 모바일 최적화 (1일)
1. **터치 인터페이스 개선**
   - 버튼 크기 모바일에 맞게 조정
   - 스와이프 제스처 추가
   - 하단 네비게이션 구현

2. **성능 최적화**
   - 이미지 압축
   - JavaScript 번들링
   - CSS 최적화

#### Phase 3: 네이티브 기능 추가 (선택사항)
1. **플러그인 설치**
   - 카메라 (영수증 촬영)
   - 파일 시스템 (오프라인 저장)
   - 푸시 알림

2. **테스트 및 디버깅**

#### Phase 4: 배포 준비 (1일)
1. **APK 서명**
2. **Play Console 등록**
3. **스토어 등록 자료 준비**

### 💡 추가 고려사항
- **백엔드 배포**: Heroku, AWS, Google Cloud 등
- **데이터베이스**: SQLite → PostgreSQL 마이그레이션
- **도메인**: HTTPS 필수
- **보안**: CORS 설정, API 키 관리

---
**사용법:**
1. 새로운 요구사항을 해당 우선순위 섹션에 추가
2. 요구사항 구현 완료 시 해당 항목 삭제
3. Claude가 완료된 내용을 CLAUDE.md에 반영