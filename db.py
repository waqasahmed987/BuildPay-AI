"""SQLite helpers (prototype storage)."""
import sqlite3
from datetime import datetime

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY, name TEXT, size TEXT, contract TEXT);
CREATE TABLE IF NOT EXISTS boq(id INTEGER PRIMARY KEY, project_id INT, code TEXT, section TEXT,
  description TEXT, unit TEXT, qty REAL, rate REAL);
CREATE TABLE IF NOT EXISTS crs(id INTEGER PRIMARY KEY, project_id INT, cr_no TEXT, boq_id INT,
  req_qty REAL, description TEXT, status TEXT, findings TEXT, brief TEXT, created TEXT);
CREATE TABLE IF NOT EXISTS docs(id INTEGER PRIMARY KEY, entity TEXT, entity_id INT, filename TEXT,
  text TEXT, uploaded TEXT);
CREATE TABLE IF NOT EXISTS measurements(id INTEGER PRIMARY KEY, project_id INT, cr_id INT, boq_id INT,
  qty REAL, mdate TEXT, verifier TEXT, evidence TEXT);
CREATE TABLE IF NOT EXISTS variations(id INTEGER PRIMARY KEY, project_id INT, var_no TEXT, cr_id INT,
  boq_id INT, data TEXT, additional REAL, value REAL, status TEXT, justification TEXT);
CREATE TABLE IF NOT EXISTS ipcs(id INTEGER PRIMARY KEY, project_id INT, ipc_no TEXT, period TEXT,
  lines_json TEXT, totals TEXT, exceptions TEXT, status TEXT, review TEXT, created TEXT);
CREATE TABLE IF NOT EXISTS approvals(id INTEGER PRIMARY KEY, entity TEXT, entity_id INT, decision TEXT,
  role TEXT, person TEXT, comment TEXT, ts TEXT);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, ts TEXT, role TEXT, actor TEXT, event TEXT,
  entity TEXT, entity_id INT, detail TEXT);
"""


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def q(sql, params=()):
    """Run a SELECT and return a list of dicts."""
    c = _conn()
    try:
        return [dict(r) for r in c.execute(sql, params).fetchall()]
    finally:
        c.close()


def ex(sql, params=()):
    """Run INSERT/UPDATE and return the last row id."""
    c = _conn()
    try:
        cur = c.execute(sql, params)
        c.commit()
        return cur.lastrowid
    finally:
        c.close()


def init_db():
    c = _conn()
    c.executescript(SCHEMA)
    c.close()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
