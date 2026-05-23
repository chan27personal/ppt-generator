# -*- coding: utf-8 -*-
"""pptgen — 구조화 입력(spec) → 표준 디자인 PPT(bytes). pptlib 엔진 재사용.
template: 'doc'(문서형 카드) | 'process'(가로 단계) | 'table'(라벨/내용 표).
페이지가 넘치면 자동 분할."""
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


def _geo(d):
    ML = 0.5
    X0 = ML; X1 = d.PW - ML
    return X0, X1, X1 - X0, d.PH - 0.5


def _header(d, spec):
    T = d.t
    X0, X1, CW, _ = _geo(d)
    y = 0.5
    eb = spec.get("eyebrow")
    if eb:
        d.shp(MSO_SHAPE.RECTANGLE, X0, y + 0.02, 0.2, 0.2, fill=T.PRI)
        d.text(X0 + 0.30, y - 0.02, CW - 2.0, 0.28, eb, 11.5, T.PRI, bold=True)
        y += 0.34
    title = spec.get("title", "제목")
    title_w = CW - (1.9 if d.PW < 9 else 2.6)
    tl = d.nlines(title, 22, title_w)
    d.text(X0, y, title_w, tl * 0.38 + 0.1, title, 22, T.INK, bold=True, anchor=MSO_ANCHOR.TOP, ls=27)
    y += tl * 0.38 + 0.08
    sub = spec.get("subtitle")
    if sub:
        sl = d.nlines(sub, 10.5, title_w)
        d.text(X0, y, title_w, sl * 0.20 + 0.08, sub, 10.5, T.SUB, anchor=MSO_ANCHOR.TOP, ls=13.5)
        y += sl * 0.20 + 0.10
    if spec.get("page", "A4P") == "A4P":
        d.iso_stack(d.PW - 1.35, 0.92, 1.5, 0.13, n=4, gap=0.36)
    d.shp(MSO_SHAPE.RECTANGLE, X0, y + 0.04, CW, 0.02, fill=T.LINE)
    return y + 0.20


def _bullets_height(d, bl, inner, sz):
    h = 0.0
    for b in bl:
        if isinstance(b, (tuple, list)):
            h += d.rbh(inner, b[0], b[1], sz, ind=0.16, gap=0.05)
        else:
            h += d.nlines(str(b), sz, inner - 0.16) * (sz * 1.34) / 72 + 0.05
    return h


def _draw_bullets(d, x, y, inner, bl, sz):
    T = d.t
    for b in bl:
        if isinstance(b, (tuple, list)):
            y = d.rbullet(x, y, inner, b[0], b[1], sz, ind=0.16, gap=0.05)
        else:
            lines = d.wrap(str(b), sz, inner - 0.16)
            ls = sz * 1.34
            d.shp(MSO_SHAPE.OVAL, x, y + (ls / 72) / 2 - 0.025, 0.05, 0.05, fill=T.PRI)
            d.text(x + 0.16, y, inner - 0.16, len(lines) * ls / 72 + 0.02, str(b), sz, T.INK,
                   anchor=MSO_ANCHOR.TOP, ls=ls)
            y += len(lines) * ls / 72 + 0.05
    return y


# ---------------- 문서형 (카드 세로 나열) ----------------
def _body_doc(d, spec, y):
    T = d.t
    X0, X1, CW, bottom = _geo(d)
    inner = CW - 0.36
    for sec in spec.get("sections", []):
        bl = sec.get("bullets", [])
        card_h = 0.40 + _bullets_height(d, bl, inner, 9.3) + 0.12
        if y + card_h > bottom:
            d.page(); y = 0.5
        d.shp(MSO_SHAPE.ROUNDED_RECTANGLE, X0, y, CW, card_h, fill=T.WHITE, line=T.LINE, lw=1.0, radius=0.05)
        d.shp(MSO_SHAPE.RECTANGLE, X0 + 0.16, y + 0.16, 0.06, 0.20, fill=T.PRI)
        d.text(X0 + 0.30, y + 0.10, CW - 0.5, 0.30, sec.get("heading", ""), 12, T.INK, bold=True)
        _draw_bullets(d, X0 + 0.22, y + 0.46, inner, bl, 9.3)
        y += card_h + 0.16
    return y


# ---------------- 프로세스형 (가로 단계 카드) ----------------
def _body_process(d, spec, y):
    T = d.t
    X0, X1, CW, bottom = _geo(d)
    secs = spec.get("sections", [])
    per_row = 4 if len(secs) >= 4 else max(1, len(secs))
    gap = 0.22
    cardw = (CW - gap * (per_row - 1)) / per_row
    inner = cardw - 0.20
    hdr_h = 0.62
    sz = 7.4
    n = 0
    while n < len(secs):
        row = secs[n:n + per_row]
        body_h = max(_bullets_height(d, s.get("bullets", []), inner, sz) + 0.10 for s in row)
        row_h = hdr_h + body_h
        if y + row_h > bottom:
            d.page(); y = 0.5
        for i, sec in enumerate(row):
            cx = X0 + i * (cardw + gap)
            d.shp(MSO_SHAPE.ROUNDED_RECTANGLE, cx, y, cardw, row_h, fill=T.WHITE, line=T.LINE, lw=1.0, radius=0.06)
            d.shp(MSO_SHAPE.ROUND_2_SAME_RECTANGLE, cx, y, cardw, hdr_h, fill=T.PRI, radius=0.14)
            d.shp(MSO_SHAPE.OVAL, cx + 0.10, y + 0.10, 0.28, 0.28, fill=T.PRI_D, line=None)
            d.text(cx + 0.10, y + 0.09, 0.28, 0.28, str(n + i + 1), 11, T.WHITE, bold=True, align=PP_ALIGN.CENTER)
            d.text(cx + 0.44, y + 0.10, cardw - 0.52, hdr_h - 0.16, sec.get("heading", ""), 8.6, T.WHITE, bold=True, ls=10)
            _draw_bullets(d, cx + 0.12, y + hdr_h + 0.08, inner, sec.get("bullets", []), sz)
            if i < len(row) - 1:
                d.chevron(cx + cardw + gap / 2, y + hdr_h / 2, 0.16, T.PRI, 2.2)
        y += row_h + 0.22
        n += per_row
    return y


# ---------------- 표형 (라벨 / 내용) ----------------
def _body_table(d, spec, y):
    T = d.t
    X0, X1, CW, bottom = _geo(d)
    lab_w = 1.7
    cont_x = X0 + lab_w
    cont_w = CW - lab_w
    inner = cont_w - 0.30
    sz = 9.0
    for sec in spec.get("sections", []):
        bl = sec.get("bullets", [])
        row_h = max(0.42, _bullets_height(d, bl, inner, sz) + 0.20)
        if y + row_h > bottom:
            d.page(); y = 0.5
        d.shp(MSO_SHAPE.RECTANGLE, X0, y, lab_w, row_h, fill=T.TINT, line=T.LINE, lw=0.75)
        d.text(X0 + 0.10, y, lab_w - 0.2, row_h, sec.get("heading", ""), 9.5, T.INK, bold=True, align=PP_ALIGN.LEFT)
        d.shp(MSO_SHAPE.RECTANGLE, cont_x, y, cont_w, row_h, fill=T.WHITE, line=T.LINE, lw=0.75)
        _draw_bullets(d, cont_x + 0.14, y + 0.10, inner, bl, sz)
        y += row_h
    return y


def _footer(d, spec, y):
    T = d.t
    X0, X1, CW, bottom = _geo(d)
    footer = spec.get("footer")
    if not footer:
        return y
    fh = 0.5
    if y + fh > bottom:
        d.page(); y = 0.5
    d.shp(MSO_SHAPE.ROUNDED_RECTANGLE, X0, y, CW, fh, fill=T.PRI, radius=0.10)
    d.text(X0 + 0.25, y, 1.2, fh, "산출물", 10, T.WHITE, bold=True)
    d.text(X0 + 1.35, y, CW - 1.5, fh, footer, 8.5, T.WHITE, anchor=MSO_ANCHOR.MIDDLE, ls=11)
    return y + fh


def build(spec) -> bytes:
    theme = THEMES.get(spec.get("theme", "Modern"), Modern)
    d = Deck(page=spec.get("page", "A4P"), theme=theme, font=(spec.get("font") or None))
    d.page()
    y = _header(d, spec)
    tmpl = spec.get("template", "doc")
    if tmpl == "process":
        y = _body_process(d, spec, y)
    elif tmpl == "table":
        y = _body_table(d, spec, y)
    else:
        y = _body_doc(d, spec, y)
    _footer(d, spec, y)
    buf = BytesIO()
    d.prs.save(buf)
    return buf.getvalue()
