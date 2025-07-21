# 외부 IP 접속 설정 가이드

## 개발 환경에서 외부 IP 접속 허용

### 1. 개발 서버 실행 (외부 접속 허용)
```bash
npm run dev:external
# 또는
pnpm dev:external
# 또는
yarn dev:external
```

### 2. 프로덕션 빌드 후 외부 접속 허용
```bash
# 빌드
npm run build

# 외부 접속 허용하여 시작
npm run start:external
```

### 3. 수동으로 호스트 지정
```bash
# 개발 서버
next dev -H 0.0.0.0 -p 3000

# 프로덕션 서버
next start -H 0.0.0.0 -p 3000
```

## 방화벽 설정

### Windows 방화벽
1. Windows 방화벽 고급 설정 열기
2. 인바운드 규칙 → 새 규칙
3. 포트 선택 → TCP → 특정 포트: 3000
4. 연결 허용 선택
5. 도메인, 개인, 공용 모두 선택
6. 이름: "Next.js Frontend" 입력

### 방화벽 명령어 (관리자 권한)
```powershell
# Windows 방화벽 규칙 추가
netsh advfirewall firewall add rule name="Next.js Frontend" dir=in action=allow protocol=TCP localport=3000
```

## 네트워크 설정

### 로컬 네트워크 접속
- 로컬 IP 주소 확인: `ipconfig` (Windows) 또는 `ifconfig` (Linux/Mac)
- 브라우저에서 `http://[로컬IP]:3000` 접속

### 외부 네트워크 접속
1. 공유기 포트 포워딩 설정 (3000번 포트)
2. 공인 IP 주소 확인
3. 브라우저에서 `http://[공인IP]:3000` 접속

## 보안 고려사항

### 개발 환경
- 개발 환경에서는 `0.0.0.0` 바인딩 사용 가능
- 프로덕션에서는 특정 IP 주소로 제한 권장

### 프로덕션 환경
```bash
# 특정 IP로 제한
next start -H 192.168.1.100 -p 3000

# 또는 환경 변수 사용
HOST=192.168.1.100 PORT=3000 next start
```

## 문제 해결

### 포트가 이미 사용 중인 경우
```bash
# 포트 사용 확인
netstat -ano | findstr :3000

# 다른 포트 사용
next dev -H 0.0.0.0 -p 3001
```

### 접속이 안 되는 경우
1. 방화벽 설정 확인
2. 네트워크 연결 상태 확인
3. 서버 로그 확인
4. 브라우저 개발자 도구에서 네트워크 탭 확인 