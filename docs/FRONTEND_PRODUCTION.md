# 프론트엔드(Next.js) 성능·보안 설정

## 1. 적용된 설정 요약

### 보안 헤더 (`next.config.mjs`)

| 헤더 | 값 | 설명 |
|------|-----|------|
| X-Frame-Options | DENY | iframe 삽입 방지 |
| X-Content-Type-Options | nosniff | MIME 스니핑 방지 |
| X-XSS-Protection | 1; mode=block | XSS 필터 활성화 |
| Referrer-Policy | strict-origin-when-cross-origin | 외부 전달 시 referrer 제한 |
| Permissions-Policy | camera=(), microphone=(), geolocation=() | 불필요한 브라우저 API 비허용 |
| Cache-Control (페이지) | public, max-age=0, must-revalidate | 기본 캐시 정책 |

### 성능

- **compress: true** – Next.js가 gzip 등 압축 응답 (프로덕션 기본)
- **_next/static/** – `Cache-Control: public, max-age=31536000, immutable` 로 장기 캐시

## 2. Nginx 뒤에서 프론트엔드 사용 시 (단일 80 포트)

`nginx/sales-portal.conf` 에서 80 포트로 다음처럼 동작합니다.

- **/** → Next.js (127.0.0.1:3000)
- **/api/** → Django (8000)
- **/admin/** → Django (8000)
- **/static/** → 백엔드 정적 파일

이 구성을 쓰면 **API를 같은 호스트의 `/api`로** 쓰는 것이 좋습니다.

```bash
# frontend/.env.production 또는 배포 시 사용
NEXT_PUBLIC_API_URL=http://168.107.7.140/api
```

(포트 없이 같은 호스트를 쓰면 Nginx가 `/api`를 Django로 프록시합니다.)

- 개발 시에는 기존처럼 `NEXT_PUBLIC_API_URL=http://168.107.7.140:8000/api` 사용 가능.

## 3. 실행 순서 (통합 구성)

1. **백엔드** (8000):  
   `cd backend && . venv/bin/activate && RUN_PRODUCTION=1 python manage.py runserver 0.0.0.0:8000`

2. **프론트엔드** (3000):  
   `cd frontend && npm run build && npm run start`  
   또는 개발: `npm run dev`

3. **Nginx** (80):  
   `sudo cp nginx/sales-portal.conf /etc/nginx/conf.d/`  
   `sudo nginx -t && sudo systemctl reload nginx`

접속: `http://168.107.7.140/` → Next.js, `http://168.107.7.140/admin/` → Django Admin.

## 4. 추가로 고려할 보안 (선택)

- **HTTPS**: 실제 서비스 시 Let's Encrypt + Nginx SSL 설정 권장.
- **CSP(Content-Security-Policy)**: 필요 시 `next.config.mjs`의 `headers()`에 추가 (정책이 엄하면 스크립트/스타일 도메인 화이트리스트 필요).
