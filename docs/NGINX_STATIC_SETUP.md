# Nginx에서 /static/ 직접 서빙 설정 가이드
# Django admin CSS 등 정적 파일을 Nginx가 직접 제공하면 성능·보안에 유리합니다.

## 1. 동작 방식

- **/static/** 요청 → Nginx가 `backend/staticfiles/` 디렉토리에서 직접 응답 (Django 거치지 않음)
- **그 외 /** 요청 → Django(127.0.0.1:8000)로 프록시

## 2. 사전 준비

```bash
# 정적 파일 수집 (이미 했다면 생략)
cd /home/ubuntu/sales-portal/backend
. venv/bin/activate
DJANGO_SETTINGS_MODULE=settings.production python manage.py collectstatic --noinput
```

## 3. 설정 방법

### 방법 A: 기존 server 블록에 location만 추가

이미 Nginx에서 Django를 프록시하고 있다면, 해당 `server` 블록 안에 아래만 추가합니다.

```nginx
location /static/ {
    alias /home/ubuntu/sales-portal/backend/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, immutable";
    access_log off;
}
```

추가 후:

```bash
sudo nginx -t && sudo systemctl restart nginx
```

### 방법 B: 새 사이트로 전체 설정 (권장)

Nginx가 80 포트에서 받아서 Django(8000)로 넘기고, `/static/`만 직접 서빙하는 **전체 server 블록** 예시입니다.

**1) 설정 파일 생성**

```bash
sudo tee /etc/nginx/conf.d/sales-portal.conf <<'EOF'
server {
    listen 80;
    server_name 168.107.7.140;   # 필요 시 _ 또는 도메인으로 변경

    # 정적 파일: Nginx가 직접 서빙 (Django 미경유)
    location /static/ {
        alias /home/ubuntu/sales-portal/backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # 나머지 요청은 Django로 프록시
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

**2) 설정 검사 및 재시작**

```bash
sudo nginx -t
sudo systemctl restart nginx
# 또는: sudo service nginx restart
```

**3) Django는 8000에서만 실행**

Nginx가 80을 받으므로, Django는 `runserver 0.0.0.0:8000` 또는 gunicorn 등으로 **8000 포트**에서만 실행하면 됩니다.

- 접속: `http://168.107.7.140/` (80 포트, Nginx 경유)
- `/static/` → Nginx가 직접 응답
- `/admin/`, `/api/` 등 → Nginx가 8000으로 프록시

### 방법 C: 80 포트 없이 Nginx가 8000과 같은 포트를 쓰는 경우

Django를 8000이 아닌 다른 포트(예: 8080)에서 띄우고, Nginx가 8000을 받아서 정적은 직접 서빙·나머지는 Django로 넘기는 방식도 가능합니다. 위 예시에서 `listen 80`을 `listen 8000`으로, `proxy_pass`를 `http://127.0.0.1:8080` 등으로 바꾸면 됩니다.

## 4. 경로가 다른 서버에서 사용할 때

프로젝트 경로가 `/home/ubuntu/sales-portal`가 아니면 다음만 수정하면 됩니다.

- `alias` 경로: `.../backend/staticfiles/` (끝에 `/` 유지)
- 예: `/opt/sales-portal/backend/staticfiles/`

## 5. 확인

```bash
# 정적 파일 직접 요청 (200 + CSS 내용 나오면 성공)
curl -I http://168.107.7.140/static/admin/css/base.css

# Admin 페이지 (브라우저에서 스타일 적용 여부 확인)
# http://168.107.7.140/admin/
```

## 6. 정리

| 구분 | Django만 사용 (현재) | Nginx 적용 후 |
|------|----------------------|-------------------------------|
| 정적 파일 | Django가 응답 | Nginx가 직접 응답 |
| 성능 | 매 요청마다 Django 경유 | 정적은 디스크에서만 처리 |
| 캐시 | 제한적 | `expires 30d` 등으로 제어 가능 |

이 설정을 쓰면 `urls.py`에서 정적 파일을 서빙하는 코드가 있어도, Nginx가 먼저 `/static/`을 처리하므로 Nginx 사용이 우선됩니다.
