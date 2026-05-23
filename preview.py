# -*- coding: utf-8 -*-
"""preview — pptx(bytes)를 PNG 이미지 리스트로 변환 (미리보기용).
LibreOffice(soffice)로 PDF 변환 → PyMuPDF(fitz)로 페이지 래스터화.
soffice/pymupdf가 없으면 빈 결과 + 사유를 반환(앱은 다운로드만 제공)."""
import os, glob, shutil, tempfile, subprocess
from pathlib import Path


def _soffice():
    for c in ("soffice", "libreoffice"):
        p = shutil.which(c)
        if p:
            return p
    for p in (r"C:\Program Files\LibreOffice\program\soffice.exe",
              r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
              "/usr/bin/soffice", "/usr/bin/libreoffice", "/snap/bin/libreoffice",
              "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if os.path.exists(p):
            return p
    return None


def to_images(pptx_bytes, dpi=110, max_pages=3):
    """returns (list[png_bytes], error_or_None)"""
    soffice = _soffice()
    if not soffice:
        return [], "LibreOffice(soffice) 미설치 — 미리보기 생략"
    try:
        import fitz  # PyMuPDF
    except Exception:
        return [], "pymupdf 미설치 — 미리보기 생략"

    tmp = tempfile.mkdtemp(prefix="pptprev_")
    try:
        pptx_path = os.path.join(tmp, "in.pptx")
        with open(pptx_path, "wb") as f:
            f.write(pptx_bytes)
        profile = Path(os.path.join(tmp, "loprofile")).as_uri()  # 동시 실행 충돌 방지
        cmd = [soffice, f"-env:UserInstallation={profile}", "--headless", "--norestore",
               "--nolockcheck", "--convert-to", "pdf", "--outdir", tmp, pptx_path]
        subprocess.run(cmd, check=True, timeout=120,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pdfs = glob.glob(os.path.join(tmp, "*.pdf"))
        if not pdfs:
            return [], "PDF 변환 실패"
        doc = fitz.open(pdfs[0])
        imgs = []
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            pix = page.get_pixmap(dpi=dpi)
            imgs.append(pix.tobytes("png"))
        doc.close()
        return imgs, None
    except subprocess.TimeoutExpired:
        return [], "변환 시간 초과"
    except Exception as e:
        return [], f"미리보기 오류: {e}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
