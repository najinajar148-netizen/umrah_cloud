#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗄️ مدير قاعدة البيانات - Streamlit Edition"""

import sqlite3
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd


# ==================== تطبيع الأسماء ====================
def normalize_arabic_name(name) -> str:
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return ""
    import unicodedata
    import re
    name = str(name).strip()
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    replacements = {'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ء': '', 'ئ': 'ي', 'ؤ': 'و',
                    'ة': 'ه', 'ى': 'ي', 'ﻻ': 'لا', 'ﻷ': 'لا', 'ﻹ': 'لي', 'ﻵ': 'لا'}
    for old, new in replacements.items():
        name = name.replace(old, new)
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'[^\w\s]', '', name)
    return name.strip().lower()


def clean_system_id(v):
    if v is None:
        return ""
    val = str(v).strip().upper()
    if val in ['#N/A', 'N/A', 'NAN', '']:
        return ""
    if '.' in val:
        val = val.split('.')[0]
    return val.lstrip('0')


def clean_passport(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip().upper().split('.')[0].lstrip('0')


class DatabaseManager:
    def __init__(self, db_path: str = "data/umrah_system.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @st.cache_resource
    def _init_db(_self):
        conn = sqlite3.connect(str(_self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS pilgrims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id TEXT NOT NULL UNIQUE,
                passport TEXT NOT NULL,
                name TEXT NOT NULL,
                visa TEXT DEFAULT '',
                days_in_kingdom INTEGER DEFAULT 0,
                status TEXT DEFAULT 'داخل المملكة',
                agent TEXT DEFAULT 'غير مسجل',
                system_name TEXT DEFAULT '',
                entry_date TEXT,
                visa_status TEXT DEFAULT 'لم يتم التنزيل',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_pilgrims_system_id ON pilgrims(system_id);
            CREATE INDEX IF NOT EXISTS idx_pilgrims_passport ON pilgrims(passport);
            CREATE INDEX IF NOT EXISTS idx_pilgrims_agent ON pilgrims(agent);
            CREATE INDEX IF NOT EXISTS idx_pilgrims_status ON pilgrims(status);

            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                group_id TEXT DEFAULT '',
                visa_group_id TEXT DEFAULT '',
                drive_id TEXT DEFAULT '',
                file_type TEXT DEFAULT 'PDF',
                active_pilgrims INTEGER DEFAULT 0,
                over_80_count INTEGER DEFAULT 0,
                total_pilgrims INTEGER DEFAULT 0,
                phone TEXT DEFAULT '',
                email TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_agents_name ON agents(name);

            CREATE TABLE IF NOT EXISTS visa_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pilgrim_id INTEGER,
                pilgrim_passport TEXT,
                pilgrim_name TEXT,
                agent_name TEXT,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                status TEXT DEFAULT 'downloaded',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pilgrim_id) REFERENCES pilgrims(id)
            );

            CREATE TABLE IF NOT EXISTS sent_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id INTEGER,
                agent_name TEXT,
                sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_type TEXT,
                status TEXT DEFAULT 'sent',
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            );
        """)
        conn.commit()
        return conn

    def get_connection(self):
        return sqlite3.connect(str(self.db_path))

    # ==================== دوال الإحصائيات ====================
    def get_total_count(self) -> int:
        conn = self.get_connection()
        return conn.execute("SELECT COUNT(*) FROM pilgrims").fetchone()[0]

    def get_active_count(self) -> int:
        conn = self.get_connection()
        return conn.execute("SELECT COUNT(*) FROM pilgrims WHERE status='داخل المملكة'").fetchone()[0]

    def get_over_80_count(self) -> int:
        conn = self.get_connection()
        return conn.execute("SELECT COUNT(*) FROM pilgrims WHERE days_in_kingdom >= 80 AND status='داخل المملكة'").fetchone()[0]

    def get_agents_count(self) -> int:
        conn = self.get_connection()
        return conn.execute("SELECT COUNT(*) FROM agents WHERE is_active=1").fetchone()[0]

    def get_statistics(self) -> Dict:
        return {
            'total': self.get_total_count(),
            'active': self.get_active_count(),
            'over_80': self.get_over_80_count(),
            'agents': self.get_agents_count(),
            'last_update': datetime.now().isoformat()
        }

    # ==================== دوال المعتمرين ====================
    def get_all_pilgrims(self, page: int = 1, per_page: int = 100) -> List[Dict]:
        conn = self.get_connection()
        offset = (page - 1) * per_page
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM pilgrims ORDER BY days_in_kingdom DESC LIMIT ? OFFSET ?",
                           (per_page, offset))
        return [dict(row) for row in cur.fetchall()]

    def search_pilgrims(self, query: str = "", agent: str = None, status: str = None,
                        visa_status: str = None, system_name: str = None) -> List[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM pilgrims WHERE 1=1"
        params = []
        if query:
            sql += " AND (system_id LIKE ? OR passport LIKE ? OR name LIKE ? OR visa LIKE ? OR agent LIKE ?)"
            term = f"%{query}%"
            params.extend([term, term, term, term, term])
        if agent:
            sql += " AND agent = ?"
            params.append(agent)
        if status:
            sql += " AND status = ?"
            params.append(status)
        if visa_status:
            sql += " AND visa_status = ?"
            params.append(visa_status)
        if system_name:
            sql += " AND system_name = ?"
            params.append(system_name)
        sql += " ORDER BY days_in_kingdom DESC LIMIT 1000"
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]

    def add_pilgrim(self, data: Dict) -> bool:
        conn = self.get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO pilgrims 
                (system_id, passport, name, visa, days_in_kingdom, status, agent, 
                 system_name, entry_date, visa_status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                data['system_id'], data['passport'], data['name'], data.get('visa', ''),
                data.get('days_in_kingdom', 0), data.get('status', 'داخل المملكة'),
                data.get('agent', 'غير مسجل'), data.get('system_name', ''),
                data.get('entry_date', ''), data.get('visa_status', 'لم يتم التنزيل')
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding pilgrim: {e}")
            return False

    def update_pilgrim(self, system_id: str, data: Dict) -> bool:
        conn = self.get_connection()
        try:
            conn.execute("""
                UPDATE pilgrims SET passport=?, name=?, visa=?, days_in_kingdom=?,
                status=?, agent=?, system_name=?, entry_date=?, visa_status=?,
                updated_at=CURRENT_TIMESTAMP WHERE system_id=?
            """, (
                data['passport'], data['name'], data.get('visa', ''),
                data.get('days_in_kingdom', 0), data.get('status', 'داخل المملكة'),
                data.get('agent', 'غير مسجل'), data.get('system_name', ''),
                data.get('entry_date', ''), data.get('visa_status', 'لم يتم التنزيل'),
                system_id
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating pilgrim: {e}")
            return False

    def delete_pilgrim(self, system_id: str) -> bool:
        conn = self.get_connection()
        try:
            conn.execute("DELETE FROM pilgrims WHERE system_id=?", (system_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting pilgrim: {e}")
            return False

    def import_pilgrims_bulk(self, data: List[Dict]) -> Tuple[int, int]:
        success, failed = 0, 0
        for item in data:
            if self.add_pilgrim(item):
                success += 1
            else:
                failed += 1
        return success, failed

    # ==================== دوال الوكلاء ====================
    def get_all_agents(self) -> List[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM agents WHERE is_active=1 ORDER BY name")
        return [dict(row) for row in cur.fetchall()]

    def add_agent(self, data: Dict) -> bool:
        conn = self.get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO agents 
                (name, group_id, visa_group_id, drive_id, file_type, phone, email, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                data['name'], data.get('group_id', ''), data.get('visa_group_id', ''),
                data.get('drive_id', ''), data.get('file_type', 'PDF'),
                data.get('phone', ''), data.get('email', '')
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding agent: {e}")
            return False

    def update_agent(self, name: str, data: Dict) -> bool:
        conn = self.get_connection()
        try:
            conn.execute("""
                UPDATE agents SET group_id=?, visa_group_id=?, drive_id=?, file_type=?,
                phone=?, email=?, updated_at=CURRENT_TIMESTAMP WHERE name=?
            """, (
                data.get('group_id', ''), data.get('visa_group_id', ''),
                data.get('drive_id', ''), data.get('file_type', 'PDF'),
                data.get('phone', ''), data.get('email', ''), name
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating agent: {e}")
            return False

    def delete_agent(self, name: str) -> bool:
        conn = self.get_connection()
        try:
            conn.execute("UPDATE agents SET is_active=0 WHERE name=?", (name,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting agent: {e}")
            return False

    def sync_agent_stats(self):
        conn = self.get_connection()
        conn.execute("UPDATE agents SET active_pilgrims=0, over_80_count=0, total_pilgrims=0")
        results = conn.execute("""
            SELECT agent, COUNT(*) as total,
                   SUM(CASE WHEN status='داخل المملكة' THEN 1 ELSE 0 END) as active,
                   SUM(CASE WHEN days_in_kingdom>=80 AND status='داخل المملكة' THEN 1 ELSE 0 END) as over_80
            FROM pilgrims WHERE agent != 'غير مسجل' GROUP BY agent
        """).fetchall()
        for row in results:
            conn.execute("""
                UPDATE agents SET active_pilgrims=?, over_80_count=?, total_pilgrims=?
                WHERE name=?
            """, (row[1], row[3] or 0, row[0], row[1]))
        conn.commit()

    # ==================== دوال التأشيرات ====================
    def update_visa_status(self, passport: str, status: str, file_name: str = None) -> bool:
        conn = self.get_connection()
        try:
            conn.execute("UPDATE pilgrims SET visa_status=?, updated_at=CURRENT_TIMESTAMP WHERE passport=?",
                         (status, passport))
            if file_name:
                pilgrim = conn.execute("SELECT id, name, agent FROM pilgrims WHERE passport=?",
                                       (passport,)).fetchone()
                if pilgrim:
                    conn.execute("""
                        INSERT INTO visa_files (pilgrim_id, pilgrim_passport, pilgrim_name, 
                        agent_name, file_name, file_path, status) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (pilgrim[0], passport, pilgrim[1], pilgrim[2], file_name, file_name, status))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating visa status: {e}")
            return False

    def get_visa_statistics(self) -> Dict:
        conn = self.get_connection()
        stats = {}
        cur = conn.execute("""
            SELECT visa_status, COUNT(*) FROM pilgrims GROUP BY visa_status
        """)
        stats['by_status'] = {row[0]: row[1] for row in cur.fetchall()}
        stats['total_files'] = conn.execute("SELECT COUNT(*) FROM visa_files").fetchone()[0]
        return stats


# ==================== دالة Singleton للحصول على قاعدة البيانات ====================
@st.cache_resource
def get_database() -> DatabaseManager:
    return DatabaseManager("data/umrah_system.db")