#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📨 إرسال التقارير عبر واتساب"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.database import get_database
from utils.reports import generate_report
from utils.whatsapp import get_whatsapp_sender

st.set_page_config(page_title="إرسال التقارير", page_icon="📨", layout="wide")

st.markdown("# 📨 إرسال التقارير عبر واتساب")

db = get_database()
sender = get_whatsapp_sender()

# إعدادات واتساب
with st.expander("⚙️ إعدادات UltraMsg"):
    instance_id = st.text_input("Instance ID", value=sender.instance_id, type="password")
    token = st.text_input("Token", value=sender.token, type="password")
    if st.button("💾 حفظ الإعدادات"):
        sender.instance_id = instance_id
        sender.token = token
        st.success("✅ تم الحفظ")

# اختبار الاتصال
if st.button("🧪 اختبار الاتصال"):
    if sender.test_connection():
        st.success("✅ الاتصال ناجح!")
    else:
        st.error("❌ فشل الاتصال")

st.markdown("---")

agents = db.get_all_agents()
if agents:
    df_agents = pd.DataFrame(agents)
    st.dataframe(df_agents[['name', 'group_id', 'active_pilgrims']], use_container_width=True, hide_index=True)

    selected_agent = st.selectbox("اختر الوكيل للإرسال", [a['name'] for a in agents])

    if selected_agent:
        agent_data = next((a for a in agents if a['name'] == selected_agent), None)
        pilgrims = db.search_pilgrims(agent=selected_agent, status='داخل المملكة')
        df = pd.DataFrame(pilgrims)

        st.write(f"👥 المعتمرين داخل المملكة: {len(pilgrims)}")
        st.write(f"📱 المجموعة: {agent_data.get('group_id', 'غير محدد')}")

        format_type = st.radio("نوع التقرير", ["PDF", "Excel"], horizontal=True)

        if st.button("📤 إنشاء وإرسال", type="primary"):
            if not sender.is_configured():
                st.error("❌ يرجى إعداد UltraMsg أولاً")
            elif not agent_data.get('group_id'):
                st.error("❌ الوكيل لا يملك ID مجموعة")
            else:
                try:
                    report_path = generate_report(df, selected_agent, format_type)
                    over_80 = len(df[df['days_in_kingdom'] >= 80]) if 'days_in_kingdom' in df.columns else 0
                    result = sender.send_report_to_agent(
                        selected_agent, agent_data['group_id'], report_path,
                        len(pilgrims), over_80
                    )
                    if result['success']:
                        st.success(f"✅ تم الإرسال إلى {selected_agent}")
                    else:
                        st.error(f"❌ فشل: {result.get('error', '')}")
                except Exception as e:
                    st.error(f"❌ خطأ: {e}")