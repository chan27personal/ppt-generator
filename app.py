# -*- coding: utf-8 -*-
"""PPT 자동 생성 + 자료실 (Streamlit).
- 생성: 입력 → 템플릿 선택 → PPT 생성 → 미리보기 → 다운로드 → 자료실 저장
- 자료실: 업로드·검색·버전관리·다운로드·삭제 (단일 인스턴스 공유)
실행:  streamlit run app.py
"""
import os, datetime as _dt
import streamlit as st

# Streamlit Cloud의 secrets(TOML)에 DATABASE_URL을 넣으면 환경변수로 넘겨준다.
# (store.py는 DATABASE_URL 환경변수를 읽어 Supabase/PostgreSQL에 연결 → 자료실 영구화)
try:
    if "DATABASE_URL" in st.secrets:
        os.environ["DATABASE_URL"] = str(st.secrets["DATABASE_URL"])
except Exception:
    pass

import pptgen, preview, store

st.set_page_config(page_title="PPT 자동 생성", page_icon="📑", layout="wide")

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


def _fmt(ts):
    try:
        return _dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "-"


# ---------------- 사이드바 (공통 설정) ----------------
with st.sidebar:
    st.header("⚙️ 설정")
    theme = st.selectbox("테마", ["Modern", "Navy"],
                         format_func=lambda x: {"Modern": "모던(로열블루)", "Navy": "네이비(정형)"}[x])
    page = st.selectbox("크기", ["A4P", "16:9"],
                        format_func=lambda x: {"A4P": "A4 세로", "16:9": "16:9 와이드"}[x])
    template = st.selectbox("템플릿", ["doc", "process", "table"],
                            format_func=lambda x: {"doc": "문서형(카드)", "process": "프로세스형(가로 단계)",
                                                   "table": "표형(라벨·내용)"}[x])
    font = st.text_input("글꼴", "사천항공", help="대상 PC에 설치된 폰트명. 미설치 시 PowerPoint가 대체 폰트로 표시")
    owner = st.text_input("작성자(선택)", "")
    st.divider()
    s = store.stats()
    st.caption(f"📚 자료실: 파일 {s['files']}개 · 제목 {s['titles']}종")
    _db_url = os.environ.get("DATABASE_URL", "")
    if _db_url.startswith("postgres"):
        st.caption("🔌 DB: **Postgres (영구)** ✅")
    else:
        st.caption("🔌 DB: SQLite (임시) — DATABASE_URL 미설정")

st.title("📑 PPT 자동 생성기")

tab_gen, tab_lib = st.tabs(["✏️ 생성", "🗂️ 자료실"])

# ================= 생성 탭 =================
with tab_gen:
    c1, c2 = st.columns([3, 2])
    with c1:
        eyebrow = st.text_input("상단 라벨", "성능 및 품질 · 이행 방안")
        title = st.text_input("제목", "검증된 성능 최적화로 고성능 시스템을 보장합니다")
        subtitle = st.text_area("부제", "설계 단계 목표 설정부터 안정화 단계 성능 유지까지, 전 주기 성능관리 체계로 목표성능을 측정·검증·보장합니다.", height=80)
        st.markdown("**본문** — `# 섹션제목`, 그 아래 `- 라벨: 설명` 또는 `- 일반 항목`")
        body = st.text_area("본문", DEFAULT_BODY, height=300, label_visibility="collapsed")
        footer = st.text_input("하단 산출물(선택)", "성능시험 계획서/결과서 · 가용성 테스트 계획서/결과서 · 시스템 최적화 계획서/결과서")
        fname = st.text_input("파일명/제목", "성능_및_품질_제안서")
        gen = st.button("🎯 PPT 생성", type="primary", use_container_width=True)

    if gen:
        spec = {"theme": theme, "page": page, "template": template, "font": font.strip(),
                "eyebrow": eyebrow.strip(), "title": title.strip(), "subtitle": subtitle.strip(),
                "sections": pptgen.parse_body(body), "footer": footer.strip()}
        try:
            data = pptgen.build(spec)
            st.session_state["gen"] = {
                "data": data, "fname": (fname.strip() or "presentation"),
                "theme": theme, "page": page, "template": template,
            }
            with st.spinner("미리보기 생성 중…"):
                imgs, err = preview.to_images(data, dpi=110, max_pages=3)
            st.session_state["gen"]["imgs"] = imgs
            st.session_state["gen"]["err"] = err
        except Exception as e:
            st.error(f"생성 오류: {e}")

    with c2:
        g = st.session_state.get("gen")
        if g:
            st.success("생성 완료")
            st.download_button("⬇️ PPTX 다운로드", g["data"], file_name=f"{g['fname']}.pptx",
                               mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                               use_container_width=True)
            if st.button("💾 자료실에 저장", use_container_width=True):
                v = store.save(g["fname"], g["data"], f"{g['fname']}.pptx",
                               theme=g["theme"], page=g["page"], template=g["template"], owner=owner.strip())
                st.toast(f"자료실 저장 완료 (v{v})")
            if g.get("imgs"):
                st.caption("미리보기")
                for im in g["imgs"]:
                    st.image(im, use_container_width=True)
            elif g.get("err"):
                st.info(f"미리보기 미표시: {g['err']} (다운로드는 정상)")
        else:
            st.info("좌측에 내용을 입력하고 **PPT 생성**을 누르세요.")

# ================= 자료실 탭 =================
with tab_lib:
    st.subheader("🗂️ 자료실 / 관리")
    up1, up2 = st.columns([3, 2])
    with up1:
        upf = st.file_uploader("PPT 업로드 (.pptx)", type=["pptx"])
    with up2:
        up_title = st.text_input("제목(업로드용)", "")
        if st.button("⬆️ 업로드 저장", use_container_width=True, disabled=(upf is None)):
            if upf is not None:
                t = (up_title.strip() or upf.name.rsplit(".", 1)[0])
                v = store.save(t, upf.getvalue(), upf.name, owner=owner.strip())
                st.toast(f"업로드 저장 완료: {t} (v{v})")
                st.rerun()

    st.divider()
    q = st.text_input("🔎 검색 (제목)", "")
    show_all = st.checkbox("모든 버전 보기", value=False)
    rows = store.list_decks(q, latest_only=not show_all)
    if not rows:
        st.caption("저장된 자료가 없습니다.")
    for r in rows:
        rid, rtitle, rtheme, rpage, rtmpl, rver, rcreated, rowner, rfn = r
        a, b, c, dcol, ecol = st.columns([4, 2, 2, 2, 1])
        a.markdown(f"**{rtitle}**  ·  v{rver}")
        b.caption(f"{rtheme or '-'} / {rtmpl or '-'} / {rpage or '-'}")
        c.caption(f"{_fmt(rcreated)}\n{('@'+rowner) if rowner else ''}")
        rec = store.get(rid)
        if rec:
            dcol.download_button("⬇️", rec[1], file_name=rec[0], key=f"dl{rid}",
                                 mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
        if ecol.button("🗑️", key=f"del{rid}"):
            store.delete(rid); st.rerun()
        with st.expander(f"버전 이력 — {rtitle}"):
            for vid, vver, vcreated, vowner, vfn in store.versions(rtitle):
                vc1, vc2 = st.columns([5, 1])
                vc1.caption(f"v{vver} · {_fmt(vcreated)} · {vfn} {('@'+vowner) if vowner else ''}")
                vrec = store.get(vid)
                if vrec:
                    vc2.download_button("⬇️", vrec[1], file_name=vrec[0], key=f"vdl{vid}",
                                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")

st.divider()
st.caption("엔진: python-pptx + pptlib · 미리보기: LibreOffice + PyMuPDF · 무료 배포: Streamlit Cloud / HF Spaces")
