#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⚙️ معالجة البيانات ورفع الملفات"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.database import get_database, clean_system_id, clean_passport
from utils.helpers import calculate_days, translate_status
from utils.reports import generate_report

st.set_page_config(page_title="المعالجة", page_icon="⚙️", layout="wide")

st.markdown("# ⚙️ معالجة البيانات وإنشاء التقارير")

db = get_database()

uploaded_files = st.file_uploader("رفع ملفات التحديث (Excel)", type=['xlsx', 'xls'],
                                  accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for file in uploaded_files:
        try:
            df = pd.read_excel(file, engine='openpyxl')
            all_data.append(df)
            st.write(f"✅ {file.name}: {len(df)} سجل")
        except Exception as e:
            st.error(f"❌ {file.name}: {e}")

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        st.write(f"📊 إجمالي السجلات: {len(combined)}")

        if st.button("🔄 معالجة وتحديث قاعدة البيانات", type="primary"):
            progress_bar = st.progress(0)
            updated = 0
            not_found = 0

            for i, (_, row) in enumerate(combined.iterrows()):
                sys_id = clean_system_id(row.get('system_id', row.get('رقم المعتمر في النظام', '')))
                passport = clean_passport(row.get('passport', row.get('رقم الجواز', '')))

                # البحث عن المعتمر
                pilgrims = db.search_pilgrims(query=sys_id or passport)
                if pilgrims:
                    # تحديث
                    entry_date = str(row.get('entry_date', row.get('entry', row.get('تاريخ الدخول', '')))).strip()
                    days = calculate_days(entry_date)
                    status = translate_status(row.get('status', row.get('الحالة', '')))

                    data = {
                        'passport': passport,
                        'name': str(row.get('name', row.get('اسم المعتمر', pilgrims[0].get('name', '')))).strip(),
                        'visa': str(row.get('visa', row.get('رقم التأشيرة', ''))).strip(),
                        'days_in_kingdom': days,
                        'status': status,
                        'entry_date': entry_date,
                        'visa_status': 'تم التنزيل' if passport else 'لم يتم التنزيل',
                        'system_name': str(row.get('system_name', '')).strip(),
                        'agent': str(row.get('agent', row.get('الوكيل', pilgrims[0].get('agent', 'غير مسجل')))).strip()
                    }
                    if db.update_pilgrim(pilgrims[0]['system_id'], data):
                        updated += 1
                else:
                    not_found += 1

                progress_bar.progress((i + 1) / len(combined))

            st.success(f"✅ تم تحديث: {updated} | ⚠️ غير موجود: {not_found}")
            st.rerun()

# ==================== إنشاء التقارير ====================
st.markdown("---")
st.subheader("📊 إنشاء تقارير")

agents = db.get_all_agents()
if agents:
    agent_names = [a['name'] for a in agents]
    selected_agent = st.selectbox("اختر الوكيل", agent_names)

    if selected_agent:
        pilgrims = db.search_pilgrims(agent=selected_agent)
        df = pd.DataFrame(pilgrims)
        st.write(f"عدد المعتمرين: {len(pilgrims)}")

        format_type = st.radio("نوع التقرير", ["PDF", "Excel"], horizontal=True)

        if st.button("📄 إنشاء تقرير", type="primary"):
            try:
                file_path = generate_report(df, selected_agent, format_type)
                with open(file_path, 'rb') as f:
                    st.download_button(
                        f"📥 تحميل التقرير ({format_type})",
                        f,
                        file_name=os.path.basename(file_path),
                        mime="application/pdf" if format_type == "PDF" else
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                st.success("✅ تم إنشاء التقرير!")
            except Exception as e:
                st.error(f"❌ خطأ: {e}")