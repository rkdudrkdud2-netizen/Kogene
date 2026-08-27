# qPCR CrossCheck 제출 및 실행 안내

## 제출 파일

제공된 `qPCR_CrossCheck_Submission.zip`을 제출합니다. 작업 폴더 전체를 압축하지 마세요.

제출용 ZIP에는 다음 항목만 포함합니다.

- `app.py`: Streamlit 웹페이지
- `candidate_grouping.py`: 추천 후보 그룹화
- `cross_reactivity_data.py`: 교차반응 추천 패널
- `distribution_sources.py`: 국내외 분양처 정보
- `excel_reporting.py`: Excel 보고서 생성
- `inventory_matching.py`: 사내 자원 파일 인식 및 유사 매칭
- `specificity_engine.py`: 분석 특이도 후보 생성
- `worklist.py`: 시험 작업 목록 생성
- `requirements.txt`: Python 패키지 목록
- `README.md`: 기능 및 기본 실행 안내
- `sample_inventory.csv`: 개인정보·사내정보가 없는 테스트용 예시
- `.streamlit/config.toml`: 웹페이지 설정
- `install_and_run.cmd`: 최초 설치 및 실행
- `qPCR_CrossCheck_START.cmd`: 설치 후 앱 시작
- `qPCR_CrossCheck_STOP.cmd`: 실행 중인 앱 종료
- `start_qpcr_webapp.vbs`: 설치 후 숨김 실행
- `stop_qpcr_webapp.vbs`: 실행 중인 앱 숨김 종료
- `register_autostart.vbs`: 해당 PC의 로그인 자동 실행 등록(선택 사항)
- `remove_autostart.vbs`: 자동 실행 등록 해제

## 제출 ZIP에서 제외하는 항목

- `.venv`: 현재 PC 전용이며 용량이 크고 다른 PC에서 재사용할 수 없음
- `__pycache__`, `.pytest_cache`: 자동 생성 캐시
- `관리_표준물질 관리 양식.xlsx`: 사내 보유 자원 원본이므로 외부 제출 금지
- `Micro_CrossCheck_AI_Distribution_Banks_v2.xlsx`: 현재 기능에서 사용하지 않는 내부 참고 파일
- 실제 사용자가 업로드한 결과 및 사내 재고 파일

## 외부 PC에서 실행하는 방법

1. ZIP 압축을 원하는 폴더에 풉니다.
2. Python 3.10 이상을 설치합니다. 설치할 때 `Add Python to PATH`를 선택합니다.
3. `install_and_run.cmd`를 더블클릭합니다.
4. 최초 실행 시 인터넷을 통해 필요한 패키지를 설치합니다.
5. 설치 후 브라우저에서 `http://localhost:8501`이 열립니다.
6. 사용자가 자신의 사내 자원 CSV/XLSX를 웹페이지에서 직접 업로드합니다.
7. 해당 PC에서 로그인할 때마다 자동 실행하려면 `register_autostart.vbs`를 한 번 실행합니다.

백신이나 사내 정책에서 `.cmd` 또는 `.vbs` 실행을 차단하면, IT 담당자가 README의 수동 실행 명령을 사용해야 합니다.

## 자동 실행의 범위

자동 실행 등록 정보 자체는 ZIP에 복사되지 않습니다. 외부 PC에서도 자동 실행이 필요하면 압축을 푼 후 `register_autostart.vbs`를 한 번 실행해야 합니다. 다음 로그인부터 서버가 숨김 상태로 시작되고 기본 브라우저에서 웹페이지가 열립니다. 해제할 때는 `remove_autostart.vbs`를 실행합니다.

자동 실행을 등록한 후 폴더를 이동하거나 이름을 바꾸면 등록된 경로가 끊어집니다. 먼저 자동 실행을 해제하고 폴더를 이동한 다음 다시 등록하세요.

`localhost`는 실행 중인 해당 PC에서만 접속할 수 있습니다. 여러 사용자가 동일 주소로 접속하려면 사내 서버/VPN 환경에 별도 배포해야 합니다.

## 제출 전 확인 사항

- 사내 원본 Excel과 민감정보가 ZIP에 없는지 확인
- 제출 기관이 소스코드 제출인지 실행 가능한 배포본 제출인지 확인
- 인터넷이 차단된 심사 환경인지 확인
- Python 설치가 허용되는지 확인
- 사내망 공유가 목적이면 IT 담당자에게 서버 배포와 방화벽 개방 요청
