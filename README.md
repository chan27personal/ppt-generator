# PPT 자동 생성기 (웹앱)

내용을 입력하면 표준 디자인(로열블루/네이비)으로 **편집 가능한 PPT**를 만들어 다운로드하는 웹 서비스.
엔진은 `pptlib`(python-pptx) 재사용. **도메인 없이** 무료 서브도메인으로 배포 가능.

## 구성
| 파일 | 역할 |
|---|---|
| `app.py` | Streamlit UI (입력 폼 → 생성 → 다운로드) |
| `pptgen.py` | 입력(spec) → PPT 생성 로직 |
| `pptlib.py` | 디자인 엔진(헬퍼 라이브러리) |
| `requirements.txt` | 파이썬 의존성 |
| `packages.txt` | 서버 폰트(`fonts-nanum`) — Streamlit Cloud용 |

## 로컬 실행
```bash
pip install -r requirements.txt
streamlit run app.py        # http://localhost:8501
```

## 무료 배포 (도메인 불필요, HTTPS 자동)

### 방법 A — Streamlit Community Cloud  → `https://<이름>.streamlit.app`
1. 이 폴더를 **GitHub 공개 저장소**에 올린다.
2. https://share.streamlit.io 에서 GitHub 로그인 → New app → 저장소/`app.py` 선택 → Deploy.
3. 끝. 생성된 `*.streamlit.app` 링크를 공유하면 **누구나 접속**해서 사용.
   - `packages.txt`의 `fonts-nanum`이 서버에 한글 폰트를 설치(줄바꿈 정확도용).

### 방법 B — HuggingFace Spaces  → `https://<계정>-<이름>.hf.space`
1. https://huggingface.co/spaces → Create new Space → SDK: **Streamlit**.
2. `app.py`, `pptgen.py`, `pptlib.py`, `requirements.txt` 업로드(또는 git push).
3. 자동 빌드 후 공개 링크 제공.

> **도메인은 나중에**: 위 무료 서브도메인으로 시작하고, 정식 서비스가 되면
> 구매한 도메인(.com 연 ~1.5만원)을 플랫폼 설정에서 연결하면 됩니다.

## 입력 형식 (본문)
```
# 섹션 제목
- 라벨: 설명          ← 라벨형 불릿 (라벨 굵게/강조)
- 일반 항목           ← 일반 불릿
# 다음 섹션
- ...
```

## 폰트 주의
- 생성 PPT는 글꼴 이름(예 `사천항공`)을 참조합니다. 받는 사람 PC에 해당 폰트가 없으면
  PowerPoint가 대체 폰트로 표시합니다. 사내 공통 폰트(예 `맑은 고딕`)로 바꾸면 호환성↑.

## 다음 단계(확장 아이디어)
- 미리보기(서버에 LibreOffice 설치 → 1페이지 PNG)
- 템플릿 선택/저장, 팀 자료실(관리시스템), 로그인/권한
