#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🛂 إدارة التأشيرات"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.database import get_database

st.set_page_config(page_title="التأشيرات", page_icon="🛂", layout="wide")

st.markdown("# 🛂 إدارة التأشيرات")

db = get_database()

st.info("""
📋 **تنزيل التأشيرات من Gmail:**
1. تأكد من وجود ملف `credentials.json` من Google Cloud Console
2. قم بتشغيل `visa_script.py` محلياً لتنزيل التأشيرات من Gmail
3. استخدم هذه الصفحة لإدارة حالات التأشيرات وتحميل الملفات يدوياً
""")

# ==================== تحديث حالة التأشيرة ====================
st.subheader("📝 تحديث حالة التأشيرة")
passport_input = st.text_input("رقم الجواز")
visa_status = st.selectbox("الحالة الجديدة", ["تم التنزيل", "لم يتم التنزيل", "تم الإرسال"])

if st.button("🔄 تحديث الحالة"):
    if passport_input:
        if db.update_visa_status(passport_input, visa_status):
            st.success("✅ تم التحديث!")
            st.rerun()
        else:
            st.warning("⚠️ لم يتم العثور على جواز السفر")

# ==================== رفع ملف تأشيرة ====================
st.subheader("📤 رفع ملف تأشيرة")
visa_file = st.file_uploader("اختر ملف PDF", type=['pdf'])
visa_passport = st.text_input("رقم جواز المعتمر للملف")

if visa_file and visa_passport:
    if st.button("📤 رفع وتحديث"):
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(visa_file.read())
            db.update_visa_status(visa_passport, 'تم التنزيل', os.path.basename(visa_file.name))
        st.success("✅ تم الرفع والتحديث")

# ==================== عرض إحصائيات ====================
st.subheader("📊 إحصائيات التأشيرات")
visa_stats = db.get_visa_statistics()
if visa_stats.get('by_status'):
    df_visa = pd.DataFrame(list(visa_stats['by_status'].items()), columns=['الحالة', 'العدد'])
    st.dataframe(df_visa, use_container_width=True, hide_index=True)