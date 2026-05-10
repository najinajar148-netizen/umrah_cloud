#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📊 لوحة التحكم والإحصائيات"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.database import get_database

st.set_page_config(page_title="لوحة التحكم", page_icon="📊", layout="wide")

st.markdown("# 📊 لوحة التحكم والإحصائيات")

db = get_database()
stats = db.get_statistics()

# بطاقات إحصائية
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("👥 إجمالي المعتمرين", stats['total'])
with col2:
    st.metric("🏨 داخل المملكة", stats['active'])
with col3:
    st.metric("⚠️ متجاوزين 80 يوم", stats['over_80'], delta_color="inverse")
with col4:
    st.metric("👔 عدد الوكلاء", stats['agents'])

# رسوم بيانية
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📈 نسبة داخل وخارج المملكة")
    departed = stats['total'] - stats['active']
    fig1 = go.Figure(data=[go.Pie(
        labels=['داخل المملكة', 'خارج المملكة'],
        values=[stats['active'], departed],
        marker=dict(colors=['#2ecc71', '#e74c3c']),
        hole=0.4
    )])
    fig1.update_layout(height=400, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig1, use_container_width=True)

with col_right:
    st.subheader("🚨 المتجاوزين 80 يوم")
    under_80 = stats['active'] - stats['over_80']
    fig2 = go.Figure(data=[
        go.Bar(name='أقل من 80', x=['المعتمرين'], y=[under_80], marker_color='#3498db'),
        go.Bar(name='80 يوم فأكثر', x=['المعتمرين'], y=[stats['over_80']], marker_color='#f39c12')
    ])
    fig2.update_layout(barmode='stack', height=400, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig2, use_container_width=True)

# إحصائيات التأشيرات
st.subheader("🛂 إحصائيات التأشيرات")
visa_stats = db.get_visa_statistics()
if visa_stats.get('by_status'):
    visa_df = pd.DataFrame(list(visa_stats['by_status'].items()), columns=['الحالة', 'العدد'])
    st.dataframe(visa_df, use_container_width=True, hide_index=True)

st.caption(f"🔄 آخر تحديث: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")