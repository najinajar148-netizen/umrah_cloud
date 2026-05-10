#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""👥 إدارة المعتمرين"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.database import get_database, clean_system_id, clean_passport, normalize_arabic_name

st.set_page_config(page_title="المعتمرين", page_icon="👥", layout="wide")

st.markdown("# 👥 إدارة المعتمرين")

db = get_database()

# ==================== علامات تبويب ====================
tab1, tab2, tab3 = st.tabs(["📋 عرض البيانات", "➕ إضافة معتمر", "📤 استيراد Excel"])

with tab1:
    st.subheader("📋 عرض بيانات المعتمرين")

    # فلترة
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search_query = st.text_input("🔍 بحث", placeholder="رقم جواز، اسم، تأشيرة...")
    with col2:
        filter_status = st.selectbox("الحالة", ["الكل", "داخل المملكة", "خارج المملكة"])
    with col3:
        filter_visa = st.selectbox("حالة التأشيرة", ["الكل", "تم التنزيل", "لم يتم التنزيل", "تم الإرسال"])
    with col4:
        # الحصول على قائمة الوكلاء
        agents = db.get_all_agents()
        agent_names = ["الكل"] + [a['name'] for a in agents]
        filter_agent = st.selectbox("الوكيل", agent_names)

    # جلب البيانات
    pilgrims = db.search_pilgrims(
        query=search_query,
        agent=None if filter_agent == "الكل" else filter_agent,
        status=None if filter_status == "الكل" else filter_status,
        visa_status=None if filter_visa == "الكل" else filter_visa
    )

    if pilgrims:
        df = pd.DataFrame(pilgrims)
        display_cols = ['system_id', 'name', 'passport', 'visa', 'agent', 'days_in_kingdom',
                       'status', 'visa_status', 'system_name', 'entry_date']
        display_names = ['رقم النظام', 'اسم المعتمر', 'رقم الجواز', 'رقم التأشيرة',
                        'الوكيل', 'عدد الأيام', 'الحالة', 'حالة التأشيرة', 'اسم النظام', 'تاريخ الدخول']

        display_cols = [c for c in display_cols if c in df.columns]
        df_display = df[display_cols].copy()
        df_display.columns = [display_names[i] for i, c in enumerate(display_cols) if c in df.columns]

        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # تصدير
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تحميل CSV", csv, f"pilgrims_{datetime.now().strftime('%Y%m%d')}.csv",
                          "text/csv")

        # حذف معتمر
        st.markdown("---")
        st.subheader("🗑️ حذف معتمر")
        delete_id = st.text_input("رقم المعتمر في النظام للحذف")
        if st.button("🗑️ حذف", type="secondary"):
            if delete_id and db.delete_pilgrim(clean_system_id(delete_id)):
                st.success("✅ تم الحذف")
                st.rerun()
            else:
                st.error("❌ فشل الحذف")
    else:
        st.info("لا توجد نتائج مطابقة")

with tab2:
    st.subheader("➕ إضافة معتمر جديد")
    with st.form("add_pilgrim"):
        cols = st.columns(3)
        with cols[0]:
            system_id = st.text_input("رقم المعتمر في النظام*")
            passport = st.text_input("رقم الجواز*")
            name = st.text_input("اسم المعتمر*")
            visa = st.text_input("رقم التأشيرة")
        with cols[1]:
            entry_date = st.date_input("تاريخ الدخول")
            status = st.selectbox("الحالة", ["داخل المملكة", "خارج المملكة"])
            days = st.number_input("عدد الأيام", min_value=0, value=0)
        with cols[2]:
            agent = st.text_input("الوكيل", "غير مسجل")
            system_name = st.text_input("اسم النظام")
            visa_status = st.selectbox("حالة التأشيرة", ["لم يتم التنزيل", "تم التنزيل", "تم الإرسال"])

        if st.form_submit_button("💾 حفظ", type="primary"):
            if system_id and passport and name:
                days_calc = days if days > 0 else (datetime.now().date() - entry_date).days if entry_date else 0
                data = {
                    'system_id': clean_system_id(system_id),
                    'passport': clean_passport(passport),
                    'name': name.strip(),
                    'visa': visa.strip(),
                    'days_in_kingdom': days_calc,
                    'status': status,
                    'agent': normalize_arabic_name(agent) if agent != "غير مسجل" else "غير مسجل",
                    'system_name': system_name.strip(),
                    'entry_date': str(entry_date) if entry_date else '',
                    'visa_status': visa_status
                }
                if db.add_pilgrim(data):
                    st.success("✅ تمت الإضافة بنجاح!")
                else:
                    st.error("❌ فشل الإضافة")
            else:
                st.error("❌ الحقول المطلوبة فارغة (*)")

with tab3:
    st.subheader("📤 استيراد من ملف Excel")
    uploaded_file = st.file_uploader("اختر ملف Excel", type=['xlsx', 'xls'])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            st.write(f"تم قراءة {len(df)} سجل")
            st.dataframe(df.head(10), use_container_width=True)

            if st.button("💾 استيراد", type="primary"):
                data = []
                for _, row in df.iterrows():
                    data.append({
                        'system_id': clean_system_id(row.get('system_id', row.get('رقم المعتمر في النظام', ''))),
                        'passport': clean_passport(row.get('passport', row.get('رقم الجواز', ''))),
                        'name': str(row.get('name', row.get('اسم المعتمر', ''))).strip(),
                        'visa': str(row.get('visa', row.get('رقم التأشيرة', ''))).strip(),
                        'days_in_kingdom': int(row.get('days_in_kingdom', row.get('عدد الايام', 0))),
                        'status': str(row.get('status', row.get('الحالة', 'داخل المملكة'))).strip(),
                        'agent': normalize_arabic_name(str(row.get('agent', row.get('الوكيل', 'غير مسجل')))),
                        'system_name': str(row.get('system_name', row.get('اسم النظام', ''))).strip(),
                        'entry_date': str(row.get('entry_date', row.get('تاريخ الدخول', ''))).strip(),
                        'visa_status': str(row.get('visa_status', 'لم يتم التنزيل')).strip()
                    })
                success, failed = db.import_pilgrims_bulk(data)
                st.success(f"✅ نجح: {success} | ❌ فشل: {failed}")
                st.rerun()
        except Exception as e:
            st.error(f"❌ خطأ: {e}")