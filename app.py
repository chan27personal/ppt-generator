# -*- coding: utf-8 -*-
"""PPT 자동 생성 웹앱 (Streamlit). 입력 → 표준 디자인 PPT 다운로드.
실행:  streamlit run app.py
배포:  Streamlit Community Cloud / HuggingFace Spaces (무료 서브도메인)
"""
import streamlit as st
import pptgen

st.set_page_config(page_title="PPT 자동 생성", page_icon="📑", layout="centered")

st.title("📑 PPT 자동 생성기")
st.caption("내용을 입력하면 표준 디자인(로열블루/네이비)으로 편집 가능한 PPT를 만들어 드립니다.")

DEFAULT_BODY = """# 왜 성능관리인가
- 사용자 경험: 응답 지연·오류는 사용자 이탈과 만족도 하락으로 직결
- 서비스 신뢰도: 가용성 저하·장애는 서비스 중단과 신뢰 하락을 초래
- 운영 리스크: 병목·과부하 미식별 시 장애 확산과 운영비용 증가
# 4단계 이행 프로세스
- 목표 성능 설정: 시스템·MSA 관점 응답·처리 속도 목표를 발주기관과 협의·설정
- 성능 측정 수행: 부하시험 포함 실질적 측정을 목표 충족 시까지 반복
- 측정결과 관리: 수행과정별 결과 기록·보고, 튜닝·조치사항 문서화
- 성능 유지: 안정화 기간 App/SQL 성능 추적 관리 및 개선활동 정기 보고
# 핵심 측정지표
- 가용성: WEB·WAS·DB 점검, 통합테스트 전 최소 3회
- 응답시간: 온라인·배치·데이터 응답시간 구분 측정
- App·DB 튜닝: 전문가 단계별 튜닝, 작성표준 준수 점검
"""

with st.sidebar:
    st.header("설정")
    theme = st.selectbox("테마", ["Modern", "Navy"],
                         format_func=lambda x: {"Modern": "모던(로열블루)", "Navy": "네이비(정형)"}[x])
    page = st.selectbox("크기", ["A4P", "16:9"],
                        format_func=lambda x: {"A4P": "A4 세로", "16:9": "16:9 와이드"}[x])
    font = st.text_input("글꼴", "사천항공", help="대상 PC에 설치된 폰트명. 미설치 시 PowerPoint가 대체 폰트로 표시")
    fname = st.text_input("파일명", "제안서")

eyebrow = st.text_input("상단 라벨", "성능 및 품질 · 이행 방안")
title = st.text_input("제목", "검증된 성능 최적화로 고성능 시스템을 보장합니다")
subtitle = st.text_area("부제", "설계 단계 목표 설정부터 안정화 단계 성능 유지까지, 전 주기 성능관리 체계로 목표성능을 측정·검증·보장합니다.", height=80)

st.markdown("**본문** — `# 섹션제목`, 그 아래 `- 라벨: 설명` 또는 `- 일반 항목`")
body = st.text_area("본문", DEFAULT_BODY, height=320, label_visibility="collapsed")
footer = st.text_input("하단 산출물(선택)", "성능시험 계획서/결과서 · 가용성 테스트 계획서/결과서 · 시스템 최적화 계획서/결과서")

if st.button("🎯 PPT 생성", type="primary", use_container_width=True):
    spec = {
        "theme": theme, "page": page, "font": font.strip(),
        "eyebrow": eyebrow.strip(), "title": title.strip(), "subtitle": subtitle.strip(),
        "sections": pptgen.parse_body(body),
        "footer": footer.strip(),
    }
    try:
        data = pptgen.build(spec)
        st.success("생성 완료! 아래에서 다운로드하세요.")
        st.download_button("⬇️ PPTX 다운로드", data,
                           file_name=f"{(fname.strip() or 'presentation')}.pptx",
                           mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                           use_container_width=True)
    except Exception as e:
        st.error(f"생성 중 오류: {e}")

st.divider()
st.caption("엔진: python-pptx + pptlib · 무료 배포: Streamlit Cloud / HuggingFace Spaces")
