#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗄️ مدير قاعدة البيانات المُحسَّن - متوافق مع Streamlit Cloud"""

import sqlite3
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

# ==================== دوال التطبيع والتنظيف ====================
def normalize_arabic_name(name) -> str:
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return ""
    import unicodedata, re
    name = str(name).strip()
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    replacements = {'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ء': '', 'ئ': 'ي', 'ؤ': 'و',
                    'ة': 'ه', 'ى': 'ي'}
    for old, new in replacements.items(): name = name.replace(old, new)
    name = re.sub(r'\s+', ' ', name).strip().lower()
    return name

def clean_system_id(v):
    if v is None: return ""
    val = str(v).strip().upper()
    if val in ['#N/A', 'N/A', 'NAN', '']: return ""
    return val.split('.')[0].lstrip('0')

def clean_passport(v):
    if v is None or (isinstance(v, float) and pd.isna(v)): return ""
    return str(v).strip().upper().split('.')[0].lstrip('0')

# ==================== مدير قاعدة البيانات بدون Caching ====================
class DatabaseManager:
    def __init__(self, db_path: str = "data/umrah_system.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """تهيئة الجداول - تعمل بدون caching لحل مشكلة Self"""
        conn = sqlite3.connect(str(self.db_path))
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
                status TEXT DEFAULT 'downloaded',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pilgrim_id) REFERENCES pilgrims(id)
            );
        """)
        conn.commit()

    def get_connection(self):
        return sqlite3.connect(str(self.db_path))

    # ==================== الإحصائيات ====================
    def get_total_count(self) -> int:
        return self.get_connection().execute("SELECT COUNT(*) FROM pilgrims").fetchone()[0]

    def get_active_count(self) -> int:
        return self.get_connection().execute("SELECT COUNT(*) FROM pilgrims WHERE status='داخل المملكة'").fetchone()[0]

    def get_over_80_count(self) -> int:
        return self.get_connection().execute("SELECT COUNT(*) FROM pilgrims WHERE days_in_kingdom >= 80 AND status='داخل المملكة'").fetchone()[0]

    def get_agents_count(self) -> int:
        return self.get_connection().execute("SELECT COUNT(*) FROM agents WHERE is_active=1").fetchone()[0]

    def get_statistics(self) -> Dict:
        return {
            'total': self.get_total_count(),
            'active': self.get_active_count(),
            'over_80': self.get_over_80_count(),
            'agents': self.get_agents_count()
        }

    # ==================== المعتمرين ====================
    def get_all_pilgrims(self, limit=1000) -> List[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute("SELECT * FROM pilgrims ORDER BY days_in_kingdom DESC LIMIT ?", (limit,)).fetchall()]

    def search_pilgrims(self, query="", agent=None, status=None, visa_status=None) -> List[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM pilgrims WHERE 1=1"
        params = []
        if query:
            sql += " AND (system_id LIKE ? OR passport LIKE ? OR name LIKE ? OR visa LIKE ?)"
            params.extend([f"%{query}%"]*4)
        if agent: sql += " AND agent = ?"; params.append(agent)
        if status: sql += " AND status = ?"; params.append(status)
        if visa_status: sql += " AND visa_status = ?"; params.append(visa_status)
        sql += " ORDER BY days_in_kingdom DESC LIMIT 1000"
        return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def add_pilgrim(self, data: Dict) -> bool:
        conn = self.get_connection()
        try:
            conn.execute("""INSERT OR REPLACE INTO pilgrims 
                (system_id, passport, name, visa, days_in_kingdom, status, agent, 
                 system_name, entry_date, visa_status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (data['system_id'], data['passport'], data['name'], data.get('visa',''),
                 data.get('days_in_kingdom',0), data.get('status','داخل المملكة'),
                 data.get('agent','غير مسجل'), data.get('system_name',''),
                 data.get('entry_date',''), data.get('visa_status','لم يتم التنزيل')))
            conn.commit()
            return True
        except: return False

    def update_pilgrim(self, system_id: str, data: Dict) -> bool:
        conn = self.get_connection()
        try:
            conn.execute("""UPDATE pilgrims SET passport=?, name=?, visa=?, days_in_kingdom=?,
                status=?, agent=?, system_name=?, entry_date=?, visa_status=?, updated_at=CURRENT_TIMESTAMP 
                WHERE system_id=?""",
                (data['passport'], data['name'], data.get('visa',''), data.get('days_in_kingdom',0),
                 data.get('status','داخل المملكة'), data.get('agent','غير مسجل'),
                 data.get('system_name',''), data.get('entry_date',''), data.get('visa_status',''), system_id))
            conn.commit()
            return True
        except: return False

    def delete_pilgrim(self, system_id: str) -> bool:
        try:
            self.get_connection().execute("DELETE FROM pilgrims WHERE system_id=?", (system_id,)).commit()
            return True
        except: return False

    # ==================== الوكلاء ====================
    def get_all_agents(self) -> List[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute("SELECT * FROM agents WHERE is_active=1 ORDER BY name").fetchall()]

    def add_agent(self, data: Dict) -> bool:
        conn = self.get_connection()
        try:
            conn.execute("""INSERT OR REPLACE INTO agents (name, group_id, visa_group_id, drive_id, file_type, phone, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (data['name'], data.get('group_id',''), data.get('visa_group_id',''),
                 data.get('drive_id',''), data.get('file_type','PDF'), data.get('phone','')))
            conn.commit()
            return True
        except: return False

# ==================== التهيئة الصحيحة لـ Streamlit ====================
@st.cache_resource
def get_database() -> DatabaseManager:
    """تهيئة اتصال قاعدة البيانات مرة واحدة فقط للحصة"""
    return DatabaseManager("data/umrah_system.db")
