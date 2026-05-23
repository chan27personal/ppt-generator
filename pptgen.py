# -*- coding: utf-8 -*-
"""pptgen — 구조화 입력(spec)을 받아 표준 디자인 PPT(bytes)를 생성.
pptlib 엔진 재사용. 섹션을 카드로 렌더하고 페이지가 넘치면 자동 분할.
"""
from io import BytesIO
from pptlib import Deck, Modern, Navy, MSO_SHAPE, PP_ALIGN, MSO_ANCHOR

THEMES = {"Modern": Modern, "Navy": Navy}


def parse_body(text):
    """`# 제목` = 섹션, `- 라벨: 설명` 또는 `- 일반항목` = 불릿."""
    sections, cur = [], None
    for raw in (text or "").splitlines():
        ln = raw.rstrip()
        if not ln.strip():
            continue
        if ln.lstrip().startswith("#"):
            cur = {"heading": ln.lstrip("# ").strip(), "bullets": []}
            sections.append(cur)
        elif ln.lstrip().startswith(("-", "·", "•", "*")):
            item = ln.lstrip("-·•* ").strip()
            if cur is None:
                cur = {"heading": "", "bullets": []}; sections.append(cur)
            if ":" in item:
                lab, desc = item.split(":", 1)
                cur["bullets"].append((lab.strip(), desc.strip()))
            else:
                cur["bullets"].append(item)
        else:
            if cur is None:
                cur = {"heading": ln.strip(), "bullets": []}; sections.append(cur)
    return sections


def build(spec) -> bytes:
    theme = THEMES.get(spec.get("theme", "Modern"), Modern)
    d = Deck(page=spec.get("page", "A4P"), theme=theme, font=(spec.get("font") or None))
    T = d.t
    ML = 0.5
    X0, X1 = ML, d.PW - ML
    CW = X1 - X0
    bottom = d.PH - 0.5

    d.page()

    # ---------- 헤더 ----------
    y = 0.5
    eb = spec.get("eyebrow")
    if eb:
        d.shp(MSO_SHAPE.RECTANGLE, X0, y + 0.02, 0.2, 0.2, fill=T.PRI)
        d.text(X0 + 0.30, y - 0.02, CW - 2.0, 0.28, eb, 11.5, T.PRI, bold=True)
        y += 0.34
    title = spec.get("title", "제목")
    title_w = CW - (1.9 if d.PW < 9 else 2.4)
    tl = d.nlines(title, 22, title_w)
    d.text(X0, y, title_w, tl * 0.38 + 0.1, title, 22, T.INK, bold=True, anchor=MSO_ANCHOR.TOP, ls=27)
    y += tl * 0.38 + 0.08
    sub = spec.get("subtitle")
    if sub:
        sl = d.nlines(sub, 10.5, title_w)
        d.text(X0, y, title_w, sl * 0.20 + 0.08, sub, 10.5, T.SUB, anchor=MSO_ANCHOR.TOP, ls=13.5)
        y += sl * 0.20 + 0.10
    # 아이소메트릭 히어로 (A4 세로)
    if spec.get("page", "A4P") == "A4P":
        d.iso_stack(d.PW - 1.35, 0.92, 1.5, 0.13, n=4, gap=0.36)
    d.shp(MSO_SHAPE.RECTANGLE, X0, y + 0.04, CW, 0.02, fill=T.LINE)
    y += 0.20

    # ---------- 섹션 카드 ----------
    sections = spec.get("sections") or []
    for sec in sections:
        bl = sec.get("bullets", [])
        # 카드 높이 계산
        inner = CW - 0.36
        bh = 0.0
        for b in bl:
            if isinstance(b, (tuple, list)):
                bh += d.rbh(inner, b[0], b[1], 9.3, ind=0.16, gap=0.05)
            else:
                bh += d.nlines(str(b), 9.3, inner - 0.16) * (9.3 * 1.34) / 72 + 0.05
        card_h = 0.40 + bh + 0.12
        # 페이지 넘침 → 새 페이지
        if y + card_h > bottom:
            d.page(); y = 0.5
        # 카드 배경
        d.shp(MSO_SHAPE.ROUNDED_RECTANGLE, X0, y, CW, card_h, fill=T.WHITE, line=T.LINE, lw=1.0, radius=0.05)
        # 헤딩
        d.shp(MSO_SHAPE.RECTANGLE, X0 + 0.16, y + 0.16, 0.06, 0.20, fill=T.PRI)
        d.text(X0 + 0.30, y + 0.10, CW - 0.5, 0.30, sec.get("heading", ""), 12, T.INK, bold=True)
        yy = y + 0.46
        for b in bl:
            if isinstance(b, (tuple, list)):
                yy = d.rbullet(X0 + 0.22, yy, inner, b[0], b[1], 9.3, ind=0.16, gap=0.05)
            else:
                lines = d.wrap(str(b), 9.3, inner - 0.16)
                ls = 9.3 * 1.34
                d.shp(MSO_SHAPE.OVAL, X0 + 0.22, yy + (ls / 72) / 2 - 0.025, 0.05, 0.05, fill=T.PRI)
                d.text(X0 + 0.38, yy, inner - 0.16, len(lines) * ls / 72 + 0.02, str(b), 9.3, T.INK,
                       anchor=MSO_ANCHOR.TOP, ls=ls)
                yy += len(lines) * ls / 72 + 0.05
        y += card_h + 0.16

    # ---------- 푸터 ----------
    footer = spec.get("footer")
    if footer:
        fh = 0.5
        if y + fh > bottom:
            d.page(); y = 0.5
        d.shp(MSO_SHAPE.ROUNDED_RECTANGLE, X0, y, CW, fh, fill=T.PRI, radius=0.10)
        d.text(X0 + 0.25, y, 1.2, fh, "산출물", 10, T.WHITE, bold=True)
        d.text(X0 + 1.35, y, CW - 1.5, fh, footer, 8.5, T.WHITE, anchor=MSO_ANCHOR.MIDDLE, ls=11)

    buf = BytesIO()
    d.prs.save(buf)
    return buf.getvalue()
