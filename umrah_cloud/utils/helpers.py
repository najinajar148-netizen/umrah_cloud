#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🛠️ دوال مساعدة - Streamlit Edition"""

import pandas as pd
from datetime import datetime
import re
import arabic_reshaper
from bidi.algorithm import get_display


def normalize_arabic_name(name) -> str:
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return ""
    import unicodedata
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
    if v is None or (isinstance(v, float) and pd.isna(v)):
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


def translate_status(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return 'خارج المملكة'
    status_str = str(val).strip().upper()
    if status_str in ['نعم', 'YES', 'Y', '1', 'TRUE', 'داخل المملكة']:
        return 'داخل المملكة'
    return 'خارج المملكة'


def calculate_days(entry_date_str):
    if not entry_date_str or entry_date_str in ['', 'nan', 'NaN']:
        return 0
    try:
        date_str = str(entry_date_str).replace('-', '/').strip()
        formats = ['%Y/%m/%d', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']
        for fmt in formats:
            try:
                entry_date = datetime.strptime(date_str, fmt)
                if entry_date > datetime.now():
                    continue
                return (datetime.now() - entry_date).days
            except ValueError:
                continue
        return 0
    except:
        return 0


def format_display_date(date_str):
    if not date_str:
        return ""
    return str(date_str).replace('-', '/')


def transpose_arabic_text(text):
    """عرض النص العربي بشكل صحيح"""
    if not text:
        return text
    reshaped_text = arabic_reshaper.reshape(str(text))
    bidi_text = get_display(reshaped_text)
    return bidi_text