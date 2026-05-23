# -*- coding: utf-8 -*-
"""store — 자료실/관리시스템 저장소 (SQLite + BLOB).
pptx 파일과 메타데이터를 단일 .db에 저장 → 단일 인스턴스 배포에서 팀이 공유.
같은 제목으로 저장하면 version 자동 증가(버전 관리).
영구 보존하려면 PPT_DB 환경변수로 영구 디스크 경로 지정(HF/Render).
Streamlit Cloud는 파일시스템이 휘발성이라 재시작 시 초기화됨."""
import os, sqlite3, time

DB = os.environ.get("PPT_DB", os.path.join(os.path.dirname(__file__), "library.db"))


def _conn():
    c = sqlite3.connect(DB, timeout=10)
    c.execute("""CREATE TABLE IF NOT EXISTS decks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        theme TEXT, page TEXT, template TEXT,
        version INTEGER, created_at REAL,
        owner TEXT, filename TEXT, data BLOB)""")
    return c


def save(title, data, filename, theme="", page="", template="", owner=""):
    c = _conn()
    try:
        v = c.execute("SELECT COALESCE(MAX(version),0)+1 FROM decks WHERE title=?", (title,)).fetchone()[0]
        c.execute("""INSERT INTO decks(title,theme,page,template,version,created_at,owner,filename,data)
                     VALUES(?,?,?,?,?,?,?,?,?)""",
                  (title, theme, page, template, v, time.time(), owner, filename, sqlite3.Binary(data)))
        c.commit()
        return v
    finally:
        c.close()


def list_decks(query="", latest_only=False):
    c = _conn()
    try:
        rows = c.execute("""SELECT id,title,theme,page,template,version,created_at,owner,filename
                            FROM decks WHERE title LIKE ? ORDER BY created_at DESC""",
                         (f"%{query}%",)).fetchall()
        if latest_only:
            seen, out = set(), []
            for r in rows:
                if r[1] in seen:
                    continue
                seen.add(r[1]); out.append(r)
            return out
        return rows
    finally:
        c.close()


def versions(title):
    c = _conn()
    try:
        return c.execute("""SELECT id,version,created_at,owner,filename FROM decks
                            WHERE title=? ORDER BY version DESC""", (title,)).fetchall()
    finally:
        c.close()


def get(deck_id):
    c = _conn()
    try:
        return c.execute("SELECT filename,data FROM decks WHERE id=?", (deck_id,)).fetchone()
    finally:
        c.close()


def delete(deck_id):
    c = _conn()
    try:
        c.execute("DELETE FROM decks WHERE id=?", (deck_id,)); c.commit()
    finally:
        c.close()


def stats():
    c = _conn()
    try:
        n = c.execute("SELECT COUNT(*) FROM decks").fetchone()[0]
        t = c.execute("SELECT COUNT(DISTINCT title) FROM decks").fetchone()[0]
        return {"files": n, "titles": t}
    finally:
        c.close()
