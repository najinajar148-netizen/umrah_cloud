#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""👔 إدارة الوكلاء"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.database import get_database, normalize_arabic_name

st.set_page_config(page_title="الوكلاء", page_icon="👔", layout="wide")

st.markdown("# 👔 إدارة الوكلاء")

db = get_database()

tab1, tab2 = st.tabs(["📋 عرض الوكلاء", "➕ إضافة وكيل"])

with tab1:
    agents = db.get_all_agents()
    if agents:
        df = pd.DataFrame(agents)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # تحديث إحصائيات
        if st.button("🔄 تحديث إحصائيات الوكلاء"):
            db.sync_agent_stats()
            st.success("✅ تم التحديث")
            st.rerun()
    else:
        st.info("لا يوجد وكلاء")

with tab2:
    st.subheader("➕ إضافة وكيل جديد")
    with st.form("add_agent"):
        cols = st.columns(2)
        with cols[0]:
            name = st.text_input("اسم الوكيل*")
            group_id = st.text_input("ID مجموعة التقارير")
            visa_group_id = st.text_input("ID مجموعة التأشيرات")
        with cols[1]:
            drive_id = st.text_input("Drive ID")
            file_type = st.selectbox("نوع الملف", ["PDF", "EXCEL", "XLSX"])
            phone = st.text_input("رقم الهاتف")

        if st.form_submit_button("💾 حفظ", type="primary"):
            if name:
                data = {
                    'name': normalize_arabic_name(name),
                    'group_id': group_id.strip(),
                    'visa_group_id': visa_group_id.strip(),
                    'drive_id': drive_id.strip(),
                    'file_type': file_type,
                    'phone': phone.strip()
                }
                if db.add_agent(data):
                    st.success("✅ تمت الإضافة!")
                else:
                    st.error("❌ فشل الإضافة")
            else:
                st.error("❌ اسم الوكيل مطلوب")