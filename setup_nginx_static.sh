#!/bin/bash
# Nginx 정적 파일 설정 스크립트
# 사용법: ./setup_nginx_static.sh [프로젝트 루트 경로]
# 예: ./setup_nginx_static.sh
#     ./setup_nginx_static.sh /home/ubuntu/sales-portal
#     ./setup_nginx_static.sh /opt/sales-portal

set -e

# 프로젝트 루트: 인자 있으면 사용, 없으면 스크립트 위치 기준
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${1:-$SCRIPT_DIR}"
STATIC_ROOT="$PROJECT_ROOT/backend/staticfiles"
NGINX_CONF_DIR="/etc/nginx/conf.d"
NGINX_SITE_CONF="$NGINX_CONF_DIR/sales-portal-static.conf"

# 1. Nginx 설치 확인
if ! command -v nginx &> /dev/null; then
    echo "⚠️  Nginx가 설치되어 있지 않습니다."
    echo ""
    echo "Nginx 설치 방법:"
    echo "  sudo yum install -y nginx"
    echo ""
    echo "또는 Django 자체 서빙을 사용하려면:"
    echo "  export SERVE_STATIC=true"
    echo "  (Django 서버 재시작 필요)"
    exit 1
fi

# 2. 정적 파일 디렉토리 확인
if [ ! -d "$STATIC_ROOT" ]; then
    echo "❌ 정적 파일 디렉토리가 없습니다: $STATIC_ROOT"
    echo ""
    echo "먼저 collectstatic을 실행하세요:"
    echo "  cd $PROJECT_ROOT/backend"
    echo "  source venv/bin/activate"
    echo "  export DJANGO_SETTINGS_MODULE=settings.production"
    echo "  python manage.py collectstatic --noinput"
    exit 1
fi

# 3. Nginx 설정 디렉토리 확인
if [ ! -d "$NGINX_CONF_DIR" ]; then
    echo "⚠️  Nginx 설정 디렉토리가 없습니다. 생성 중..."
    sudo mkdir -p "$NGINX_CONF_DIR"
fi

# 4. Nginx 정적 파일 설정 생성 (location 조각 - server 블록 안에 include 필요)
echo "[1] Nginx 설정 파일 생성 중..."
# alias 경로에 슬래시 유지 (중요)
sudo tee "$NGINX_SITE_CONF" > /dev/null <<EOF
# Sales Portal 정적 파일 서빙 설정 (server 블록 안에 include하여 사용)
location /static/ {
    alias ${STATIC_ROOT}/;
    expires 30d;
    add_header Cache-Control "public, immutable";
    access_log off;
}
EOF

echo "✅ 설정 파일 생성 완료: $NGINX_SITE_CONF"

# 5. 메인 Nginx 설정에 include 추가 확인
MAIN_NGINX_CONF="/etc/nginx/nginx.conf"
if [ -f "$MAIN_NGINX_CONF" ]; then
    if ! grep -q "include.*sales-portal-static.conf" "$MAIN_NGINX_CONF"; then
        echo ""
        echo "[2] 이 설정은 server 블록 안에서만 유효합니다."
        echo "    기존 server 블록(예: /etc/nginx/conf.d/default.conf) 안에 다음을 추가하세요:"
        echo "    include $NGINX_CONF_DIR/sales-portal-static.conf;"
        echo ""
        echo "    또는 전체 역방향 프록시 예시는 docs/NGINX_STATIC_SETUP.md 를 참고하세요."
    else
        echo "✅ 메인 설정에 이미 포함되어 있습니다."
    fi
fi

# 6. Nginx 설정 테스트
echo ""
echo "[3] Nginx 설정 테스트 중..."
if sudo nginx -t; then
    echo "✅ Nginx 설정이 올바릅니다."
else
    echo "❌ Nginx 설정에 오류가 있습니다."
    exit 1
fi

# 7. Nginx 재시작
echo ""
echo "[4] Nginx 재시작 중..."
sudo systemctl restart nginx || sudo service nginx restart

echo ""
echo "========================================"
echo "✅ Nginx 정적 파일 설정 완료!"
echo "========================================"
echo ""
echo "정적 파일 경로: $STATIC_ROOT"
echo "Nginx 설정 파일: $NGINX_SITE_CONF"
echo ""
echo ""
echo "테스트:"
echo "  curl -I http://168.107.7.140/static/admin/css/base.css"
echo ""
echo "전체 역방향 프록시 예시는 docs/NGINX_STATIC_SETUP.md 를 참고하세요."
echo ""

