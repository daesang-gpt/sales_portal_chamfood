# 마이그레이션 파일 관리 가이드

## 현재 상황

현재 프로젝트에는 많은 마이그레이션 파일들이 있습니다 (0001 ~ 0029 등).
이들은 개발 과정에서 DB 스키마 변경 이력을 추적한 것입니다.

## 문제점

1. **처음 DB 생성 시**: 모든 마이그레이션을 순차 실행하는 것이 비효율적
   - 일부 마이그레이션은 이미 적용된 변경사항을 되돌렸다가 다시 적용하는 등 복잡함
   - 예: `0012`에서 ID를 제거하고 company_code를 PK로 설정, `0020`에서 ID를 다시 참조하려고 시도

2. **운영서버 Git pull 시**: 새로운 마이그레이션이 추가되면 자동으로 적용됨
   - 하지만 복잡한 마이그레이션들이 많으면 오류 발생 가능성 증가

## 해결 방법

### 방법 1: 마이그레이션 파일 정리 (Squash Migrations) - 권장

Django의 `squashmigrations` 명령어를 사용하여 여러 마이그레이션을 하나로 합칩니다.

```bash
# 개발 서버에서 실행
cd backend
python manage.py squashmigrations myapi 0001 0029

# 새로운 squashed 마이그레이션 파일 생성됨
# 기존 마이그레이션 파일들은 유지되지만, 새 환경에서는 squashed 버전만 사용
```

**장점:**
- 마이그레이션 파일 수 감소
- 처음 DB 생성 시 빠름
- Git pull 시에도 안정적

**단점:**
- 기존 DB가 있는 경우 마이그레이션 상태 확인 필요

### 방법 2: 최종 상태만 반영하는 새로운 초기 마이그레이션 생성

현재 모델 상태를 기준으로 새로운 `0001_initial` 마이그레이션을 생성합니다.

```bash
# 1. 기존 마이그레이션 파일 백업
mv backend/myapi/migrations backend/myapi/migrations_backup

# 2. 새로운 migrations 디렉토리 생성
mkdir backend/myapi/migrations
touch backend/myapi/migrations/__init__.py

# 3. 현재 모델 상태로 초기 마이그레이션 생성
python manage.py makemigrations

# 4. 운영서버에서는 이 새로운 마이그레이션만 실행
```

**장점:**
- 깔끔하고 단순함
- 처음 DB 생성 시 빠름

**단점:**
- 기존 마이그레이션 이력 손실
- 기존 DB가 있는 경우 마이그레이션 상태 동기화 필요

### 방법 3: 현재 방식 유지 (--run-syncdb 사용)

`reset_oracle_db.sh`에서 이미 `--run-syncdb`를 사용하고 있습니다.
이 방식은 마이그레이션 파일을 무시하고 현재 모델 상태로 직접 테이블을 생성합니다.

**장점:**
- 마이그레이션 파일 유지 (이력 보존)
- 처음 DB 생성 시 빠름

**단점:**
- `django_migrations` 테이블과 실제 DB 상태 불일치 가능
- Git pull 시 새로운 마이그레이션 적용 시 주의 필요

## 권장 방법

**현재 상황에서는 방법 3 (--run-syncdb)을 유지하되, Git pull 시 마이그레이션 처리를 개선하는 것을 권장합니다.**

### 개선된 배포 스크립트

`deploy_from_git_with_db.sh`에서 마이그레이션 실행 전에 상태를 확인하도록 수정:

```bash
# 마이그레이션 실행 전 상태 확인
python manage.py showmigrations

# 마이그레이션 실행 (이미 적용된 것은 스킵)
python manage.py migrate --fake-initial
```

이렇게 하면:
1. 처음 DB 생성 시: `--run-syncdb`로 빠르게 생성
2. Git pull 시: 새로운 마이그레이션만 적용 (이미 적용된 것은 스킵)

