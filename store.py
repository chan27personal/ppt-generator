# -*- coding: utf-8 -*-
"""store — 자료실 저장소 (SQLAlchemy). DATABASE_URL 있으면 PostgreSQL(영구·공유),
없으면 로컬 SQLite. 같은 제목 저장 시 version 자동 증가(버전관리).
파일은 BLOB/BYTEA로 DB에 저장 → 백업 한 곳(DB)으로 끝."""
import os, time
from sqlalchemy import (create_engine, MetaData, Table, Column, Integer, String,
                        Float, LargeBinary, select, insert, delete as sa_delete, func)

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///" + os.path.join(os.path.dirname(__file__), "library.db")
if DATABASE_URL.startswith("postgres://"):              # Heroku식 URL 정규화
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
_meta = MetaData()
decks = Table(
    "decks", _meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", String(500), nullable=False),
    Column("theme", String(50)), Column("page", String(20)), Column("template", String(20)),
    Column("version", Integer), Column("created_at", Float),
    Column("owner", String(200)), Column("filename", String(500)),
    Column("data", LargeBinary),
)

_ready = False
def _init():
    """DB 준비(테이블 생성). Postgres 컨테이너 기동 지연 대비 재시도."""
    global _ready
    if _ready:
        return
    last = None
    for _ in range(15):
        try:
            _meta.create_all(engine)
            _ready = True
            return
        except Exception as e:
            last = e
            time.sleep(2)
    raise last


def save(title, data, filename, theme="", page="", template="", owner=""):
    _init()
    with engine.begin() as c:
        v = c.execute(select(func.coalesce(func.max(decks.c.version), 0) + 1)
                      .where(decks.c.title == title)).scalar() or 1
        c.execute(insert(decks).values(
            title=title, theme=theme, page=page, template=template,
            version=int(v), created_at=time.time(), owner=owner,
            filename=filename, data=data))
    return int(v)


def list_decks(query="", latest_only=False):
    _init()
    with engine.connect() as c:
        rows = c.execute(
            select(decks.c.id, decks.c.title, decks.c.theme, decks.c.page, decks.c.template,
                   decks.c.version, decks.c.created_at, decks.c.owner, decks.c.filename)
            .where(decks.c.title.like(f"%{query}%"))
            .order_by(decks.c.created_at.desc())).all()
    rows = [tuple(r) for r in rows]
    if latest_only:
        seen, out = set(), []
        for r in rows:
            if r[1] in seen:
                continue
            seen.add(r[1]); out.append(r)
        return out
    return rows


def versions(title):
    _init()
    with engine.connect() as c:
        rows = c.execute(
            select(decks.c.id, decks.c.version, decks.c.created_at, decks.c.owner, decks.c.filename)
            .where(decks.c.title == title).order_by(decks.c.version.desc())).all()
    return [tuple(r) for r in rows]


def get(deck_id):
    _init()
    with engine.connect() as c:
        r = c.execute(select(decks.c.filename, decks.c.data).where(decks.c.id == deck_id)).first()
    return (r[0], bytes(r[1])) if r else None


def delete(deck_id):
    _init()
    with engine.begin() as c:
        c.execute(sa_delete(decks).where(decks.c.id == deck_id))


def stats():
    _init()
    with engine.connect() as c:
        n = c.execute(select(func.count()).select_from(decks)).scalar() or 0
        t = c.execute(select(func.count(func.distinct(decks.c.title)))).scalar() or 0
    return {"files": int(n), "titles": int(t)}
