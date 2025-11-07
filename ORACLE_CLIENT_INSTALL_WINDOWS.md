# Windows에서 Oracle Instant Client 설치 가이드

## 1. Oracle Instant Client 다운로드

1. Oracle 공식 웹사이트 방문: https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html
2. "Basic Package" 다운로드 (약 100MB)
   - 예: `instantclient-basic-windows.x64-19.20.0.0.0dbru.zip`
3. "SDK Package" 다운로드 (cx_Oracle 컴파일용, 선택사항)
   - 예: `instantclient-sdk-windows.x64-19.20.0.0.0dbru.zip`

## 2. 설치

1. 다운로드한 ZIP 파일을 `C:\oracle\instantclient_19_20`에 압축 해제
2. 환경 변수 설정:
   - `PATH`에 `C:\oracle\instantclient_19_20` 추가
   - (선택) `ORACLE_HOME`을 `C:\oracle\instantclient_19_20`로 설정

## 3. cx_Oracle 설치

```powershell
cd C:\Users\ds\Projects\sales-portal\backend
.\venv\Scripts\activate
pip install cx_Oracle
```

## 대안: oracledb 사용 (권장)

`oracledb`는 Oracle Instant Client 없이도 작동하며, 이미 설치되었습니다.
Django 설정에서 `django.db.backends.oracle`을 사용하면 자동으로 `oracledb`를 사용합니다.

Django 4.2+ 버전은 `oracledb`를 기본 지원합니다.

