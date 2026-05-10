#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕋 نظام متابعة المعتمرين - وكالة النجار للسفريات
Umrah Tracking System v7.0 - Streamlit Cloud Edition
"""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime

# إعداد الصفحة الرئيسية
st.set_page_config(
    page_title="وكالة النجار | متابعة المعتمرين",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': '🕋 نظام متابعة المعتمرين v7.0 | وكالة النجار للسفريات والسياحة'
    }
)

# إضافة مسار المجلدات
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# CSS مخصص للتنسيق العربي
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap');

    * {
        font-family: 'Tajawal', sans-serif;
        direction: rtl;
    }

    .main-header {
        font-size: 2.5rem;
        font-weight: 900;
        color: #1a5276;
        text-align: center;
        margin-bottom: 1rem;
    }

    .sub-header {
        font-size: 1.2rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
    }

    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }

    .stat-card.success {
        background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
    }

    .stat-card.warning {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
    }

    .stat-card.info {
        background: linear-gradient(135deg, #2980b9 0%, #3498db 100%);
    }

    .footer {
        text-align: center;
        padding: 2rem;
        color: #7f8c8d;
        font-size: 0.9rem;
    }

    /* تحسين مظهر الأزرار */
    .stButton > button {
        border-radius: 10px;
        font-family: 'Tajawal', sans-serif;
        font-weight: 700;
        transition: all 0.3s ease;
    }

    /* مظهر الجداول */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)


# ==================== صفحة الترحيب ====================
def show_welcome():
    st.markdown('<div class="main-header">🕋 نظام متابعة المعتمرين</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">وكالة النجار للسفريات والسياحة | Al-Najjar Travel Pro v7.0</div>', unsafe_allow_html=True)

    # إحصائيات سريعة
    from utils.database import get_database
    db = get_database()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total = db.get_total_count()
        st.markdown(f'''
        <div class="stat-card">
            <h2>👥 {total}</h2>
            <p>إجمالي المعتمرين</p>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        active = db.get_active_count()
        st.markdown(f'''
        <div class="stat-card success">
            <h2>🏨 {active}</h2>
            <p>داخل المملكة</p>
        </div>
        ''', unsafe_allow_html=True)

    with col3:
        over_80 = db.get_over_80_count()
        st.markdown(f'''
        <div class="stat-card warning">
            <h2>⚠️ {over_80}</h2>
            <p>متجاوزين 80 يوم</p>
        </div>
        ''', unsafe_allow_html=True)

    with col4:
        agents = db.get_agents_count()
        st.markdown(f'''
        <div class="stat-card info">
            <h2>👔 {agents}</h2>
            <p>عدد الوكلاء</p>
        </div>
        ''', unsafe_allow_html=True)

    # معلومات سريعة
    st.markdown("---")
    st.markdown("""
    ### 🚀 الوصول السريع
    استخدم القائمة الجانبية للتنقل بين أقسام النظام:
    - 📊 **لوحة التحكم** - الإحصائيات والرسوم البيانية
    - 👥 **المعتمرين** - إدارة بيانات المعتمرين
    - 👔 **الوكلاء** - إدارة الوكلاء ومجموعاتهم
    - ⚙️ **المعالجة** - رفع ملفات Excel ومعالجة البيانات
    - 📨 **الإرسال** - إرسال التقارير عبر واتساب
    - 🛂 **التأشيرات** - إدارة وتنزيل التأشيرات
    """)

    # تذييل
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    st.markdown(f'<div class="footer">🕋 وكالة النجار للسفريات والسياحة | {now}</div>', unsafe_allow_html=True)


# ==================== عرض الصفحة ====================
show_welcome()