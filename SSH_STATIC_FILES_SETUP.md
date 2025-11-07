# SSH에서 정적 파일 경로 연결 명령어

## 방법 1: Django 자체 서빙 (간단, 권장)

SSH로 서버에 접속한 후 다음 명령어를 순서대로 실행하세요:

```bash
# 1. 프로젝트 디렉토리로 이동
cd /opt/sales-portal/backend

# 2. 가상환경 활성화
source venv/bin/activate

# 3. 환경변수 설정
export DJANGO_SETTINGS_MODULE=settings.production
export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
export SERVE_STATIC=true

# 4. 정적 파일 수집
python manage.py collectstatic --noinput

# 5. Django 서버 재시작
# 현재 실행 중인 프로세스 확인
ps aux | grep "manage.py runserver"

# 프로세스 종료 (PID를 찾아서)
kill <PID>

# 또는 백그라운드 스크립트 사용 시
cd /opt/sales-portal
./stop_backend.sh
./start_backend_daemon.sh
```

## 방법 2: Nginx 사용 (프로덕션 권장)

### 2-1. Nginx 설치 확인 및 설치

```bash
# Nginx 설치 확인
nginx -v

# 설치되어 있지 않으면
sudo yum install -y nginx
```

### 2-2. 정적 파일 수집

```bash
cd /opt/sales-portal/backend
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=settings.production
export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
python manage.py collectstatic --noinput
```

### 2-3. Nginx 설정 파일 생성

```bash
# 설정 파일 생성
sudo tee /etc/nginx/conf.d/sales-portal-static.conf > /dev/null <<'EOF'
location /static/ {
    alias /opt/sales-portal/backend/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, immutable";
    access_log off;
}
EOF
```

### 2-4. Nginx 메인 설정에 추가

```bash
# 메인 설정 파일 편집
sudo vi /etc/nginx/nginx.conf

# 또는 자동으로 추가 (http 블록 안에)
sudo sed -i '/http {/a\    include /etc/nginx/conf.d/sales-portal-static.conf;' /etc/nginx/nginx.conf
```

**또는 server 블록에 직접 추가:**

```bash
# server 블록 찾기 (보통 /etc/nginx/conf.d/default.conf 또는 sites-enabled/)
sudo vi /etc/nginx/conf.d/default.conf

# server 블록 안에 다음 추가:
# location /static/ {
#     alias /opt/sales-portal/backend/staticfiles/;
# }
```

### 2-5. Nginx 설정 테스트 및 재시작

```bash
# 설정 테스트
sudo nginx -t

# 재시작
sudo systemctl restart nginx

# 또는
sudo service nginx restart
```

### 2-6. Nginx가 Django로 프록시하는 경우 (전체 설정 예시)

```bash
sudo tee /etc/nginx/conf.d/sales-portal.conf > /dev/null <<'EOF'
server {
    listen 80;
    server_name 192.168.99.37;

    # 정적 파일
    location /static/ {
        alias /opt/sales-portal/backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Django로 프록시
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 설정 테스트 및 재시작
sudo nginx -t && sudo systemctl restart nginx
```

## 빠른 확인 명령어

```bash
# 정적 파일 디렉토리 확인
ls -la /opt/sales-portal/backend/staticfiles/

# 정적 파일 개수 확인
find /opt/sales-portal/backend/staticfiles -type f | wc -l

# CSS 파일 확인
ls -la /opt/sales-portal/backend/staticfiles/admin/css/

# 브라우저에서 테스트
curl http://192.168.99.37/static/admin/css/base.css

# Django 서버 로그 확인
tail -f /opt/sales-portal/logs/backend.log
```

## 문제 해결

### 정적 파일이 여전히 안 보이는 경우

```bash
# 1. STATIC_ROOT 확인
cd /opt/sales-portal/backend
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=settings.production
python manage.py shell -c "from django.conf import settings; print(settings.STATIC_ROOT)"

# 2. 파일 권한 확인
ls -la /opt/sales-portal/backend/staticfiles/
sudo chown -R adm1003701:adm1003701 /opt/sales-portal/backend/staticfiles
sudo chmod -R 755 /opt/sales-portal/backend/staticfiles

# 3. Nginx 에러 로그 확인
sudo tail -f /var/log/nginx/error.log

# 4. Django 서버 재시작
cd /opt/sales-portal
./stop_backend.sh
./start_backend_daemon.sh
```

