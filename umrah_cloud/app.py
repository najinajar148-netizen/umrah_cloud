import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, date
import requests
import io
import plotly.express as px

# ======================== إعدادات الصفحة ========================
st.set_page_config(
    page_title="نظام متابعة المعتمرين",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================== دالة الاتصال بقاعدة البيانات ========================
@st.cache_resource
def init_db():
    db_path = "umrah.db"
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pilgrims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_id TEXT UNIQUE NOT NULL,
            passport TEXT NOT NULL,
            name TEXT NOT NULL,
            visa TEXT DEFAULT '',
            days_in_kingdom INTEGER DEFAULT 0,
            status TEXT DEFAULT 'داخل المملكة',
            agent TEXT DEFAULT 'غير مسجل',
            system_name TEXT DEFAULT '',
            entry_date TEXT DEFAULT '',
            visa_status TEXT DEFAULT 'لم يتم التنزيل',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            group_id TEXT DEFAULT '',
            visa_group_id TEXT DEFAULT '',
            file_type TEXT DEFAULT 'PDF',
            active_pilgrims INTEGER DEFAULT 0,
            over_80_count INTEGER DEFAULT 0,
            total_pilgrims INTEGER DEFAULT 0,
            phone TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1
        )
    """)
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_system_id ON pilgrims(system_id);
        CREATE INDEX IF NOT EXISTS idx_passport ON pilgrims(passport);
        CREATE INDEX IF NOT EXISTS idx_agent ON pilgrims(agent);
    """)
    return conn

def get_conn():
    return init_db()

# ================== دوال مساعدة ==================
def clean_id(val):
    if val is None: return ""
    return str(val).strip().upper().split('.')[0].lstrip('0')

def clean_passport(val):
    if val is None: return ""
    return str(val).strip().upper().lstrip('0')

# ================== الصفحة الرئيسية ==================
def home():
    st.markdown("<h1 style='text-align: center;'>🕋 نظام متابعة المعتمرين</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center;'>وكالة النجار للسفريات والسياحة</h4>", unsafe_allow_html=True)
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM pilgrims").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM pilgrims WHERE status='داخل المملكة'").fetchone()[0]
    over80 = conn.execute("SELECT COUNT(*) FROM pilgrims WHERE days_in_kingdom>=80 AND status='داخل المملكة'").fetchone()[0]
    agents = conn.execute("SELECT COUNT(*) FROM agents WHERE is_active=1").fetchone()[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("إجمالي المعتمرين", total)
    c2.metric("داخل المملكة", active)
    c3.metric("متجاوزين 80 يوم", over80)
    c4.metric("عدد الوكلاء", agents)

    # رسم بياني بسيط
    if total > 0:
        df = pd.DataFrame({
            'الحالة': ['داخل المملكة', 'خارج المملكة'],
            'العدد': [active, total - active]
        })
        fig = px.pie(df, names='الحالة', values='العدد', hole=0.4,
                     color_discrete_sequence=['#2ecc71', '#e74c3c'])
        st.plotly_chart(fig, use_container_width=True)

# ================== صفحة المعتمرين ==================
def pilgrims_page():
    st.header("👥 إدارة المعتمرين")
    tab1, tab2, tab3 = st.tabs(["عرض", "إضافة", "استيراد Excel"])

    conn = get_conn()
    with tab1:
        search = st.text_input("🔍 بحث برقم الجواز / الاسم / رقم التأشيرة")
        status_filter = st.radio("الحالة", ["الكل", "داخل المملكة", "خارج المملكة"], horizontal=True)

        query = "SELECT * FROM pilgrims WHERE 1=1"
        params = []
        if search:
            query += " AND (passport LIKE ? OR name LIKE ? OR visa LIKE ? OR system_id LIKE ?)"
            params += [f"%{search}%"] * 4
        if status_filter != "الكل":
            query += " AND status=?"
            params.append(status_filter)
        query += " ORDER BY days_in_kingdom DESC LIMIT 500"

        df = pd.read_sql_query(query, conn, params=params)
        st.dataframe(df, use_container_width=True, hide_index=True)

        if st.button("🗑️ حذف المعتمرين المحددين"):
            selected = st.multiselect("اختر أرقام النظام", df['system_id'].tolist())
            if selected:
                for sid in selected:
                    conn.execute("DELETE FROM pilgrims WHERE system_id=?", (sid,))
                conn.commit()
                st.rerun()

    with tab2:
        with st.form("add_pilgrim"):
            c1, c2 = st.columns(2)
            system_id = c1.text_input("رقم المعتمر في النظام*")
            passport = c2.text_input("رقم الجواز*")
            name = st.text_input("اسم المعتمر*")
            visa = st.text_input("رقم التأشيرة")
            entry_date = st.date_input("تاريخ الدخول", value=None)
            status = st.selectbox("الحالة", ["داخل المملكة", "خارج المملكة"])
            agent = st.text_input("الوكيل", "غير مسجل")
            system_name = st.text_input("اسم النظام")
            days = st.number_input("عدد الأيام", min_value=0, value=0)
            visa_status = st.selectbox("حالة التأشيرة", ["لم يتم التنزيل", "تم التنزيل", "تم الإرسال"])

            if st.form_submit_button("💾 حفظ"):
                if system_id and passport and name:
                    conn.execute("""
                        INSERT OR REPLACE INTO pilgrims 
                        (system_id, passport, name, visa, entry_date, days_in_kingdom, status, agent, system_name, visa_status)
                        VALUES (?,?,?,?,?,?,?,?,?,?)
                    """, (clean_id(system_id), clean_passport(passport), name, visa,
                          str(entry_date) if entry_date else "", days, status, agent, system_name, visa_status))
                    conn.commit()
                    st.success("تم الحفظ")
                    st.rerun()
                else:
                    st.error("الحقول الإلزامية مفقودة")

    with tab3:
        uploaded = st.file_uploader("اختر ملف Excel", type=['xlsx'])
        if uploaded:
            try:
                df = pd.read_excel(uploaded, engine='openpyxl')
                st.write(f"عدد الصفوف: {len(df)}")
                if st.button("📤 استيراد"):
                    success = 0
                    for _, row in df.iterrows():
                        try:
                            conn.execute("""
                                INSERT OR REPLACE INTO pilgrims 
                                (system_id, passport, name, visa, entry_date, days_in_kingdom, status, agent, system_name)
                                VALUES (?,?,?,?,?,?,?,?,?)
                            """, (
                                clean_id(row.get('system_id', row.get('رقم المعتمر في النظام',''))),
                                clean_passport(row.get('passport', row.get('رقم الجواز',''))),
                                row.get('name', row.get('اسم المعتمر','')),
                                row.get('visa', row.get('رقم التأشيرة','')),
                                str(row.get('entry_date', row.get('تاريخ الدخول',''))),
                                int(row.get('days_in_kingdom', row.get('عدد الايام', 0))),
                                row.get('status', row.get('الحالة','داخل المملكة')),
                                row.get('agent', row.get('الوكيل','غير مسجل')),
                                row.get('system_name', row.get('اسم النظام',''))
                            ))
                            success += 1
                        except:
                            pass
                    conn.commit()
                    st.success(f"تم استيراد {success} بنجاح")
            except Exception as e:
                st.error(str(e))

# ================== صفحة الوكلاء ==================
def agents_page():
    st.header("👔 إدارة الوكلاء")
    conn = get_conn()
    tab1, tab2 = st.tabs(["عرض", "إضافة"])
    with tab1:
        df = pd.read_sql_query("SELECT * FROM agents WHERE is_active=1", conn)
        st.dataframe(df, use_container_width=True)
        if st.button("🔄 تحديث الإحصائيات من قاعدة البيانات"):
            conn.execute("UPDATE agents SET active_pilgrims=0, over_80_count=0, total_pilgrims=0")
            results = conn.execute("""
                SELECT agent, COUNT(*),
                       SUM(CASE WHEN status='داخل المملكة' THEN 1 ELSE 0 END),
                       SUM(CASE WHEN days_in_kingdom>=80 AND status='داخل المملكة' THEN 1 ELSE 0 END)
                FROM pilgrims WHERE agent!='غير مسجل' GROUP BY agent
            """).fetchall()
            for ag, total, active, over80 in results:
                conn.execute("UPDATE agents SET total_pilgrims=?, active_pilgrims=?, over_80_count=? WHERE name=?",
                             (total, active or 0, over80 or 0, ag))
            conn.commit()
            st.rerun()
    with tab2:
        with st.form("add_agent"):
            name = st.text_input("اسم الوكيل*")
            group_id = st.text_input("ID مجموعة التقارير")
            visa_group = st.text_input("ID مجموعة التأشيرات")
            file_type = st.selectbox("نوع الملف المفضل", ["PDF","EXCEL"])
            phone = st.text_input("رقم الهاتف")
            if st.form_submit_button("حفظ"):
                if name:
                    conn.execute("INSERT OR REPLACE INTO agents (name, group_id, visa_group_id, file_type, phone) VALUES (?,?,?,?,?)",
                                 (name, group_id, visa_group, file_type, phone))
                    conn.commit()
                    st.success("تم الحفظ")
                    st.rerun()

# ================== صفحة المعالجة ==================
def processing_page():
    st.header("⚙️ معالجة ملفات التحديث")
    conn = get_conn()
    update_files = st.file_uploader("رفع ملفات التحديث (Excel)", type=['xlsx'], accept_multiple_files=True)
    if update_files:
        all_data = []
        for f in update_files:
            try:
                df = pd.read_excel(f, engine='openpyxl')
                all_data.append(df)
            except Exception as e:
                st.error(f"خطأ في {f.name}: {e}")
        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            st.write(f"عدد السجلات: {len(combined)}")
            if st.button("بدء التحديث"):
                progress = st.progress(0)
                updated = 0
                not_found = 0
                for i, (_, row) in enumerate(combined.iterrows()):
                    sid = clean_id(row.get('system_id', row.get('رقم المعتمر في النظام', '')))
                    passport = clean_passport(row.get('passport', row.get('رقم الجواز', '')))
                    # البحث عن المعتمر
                    exist = conn.execute("SELECT system_id FROM pilgrims WHERE system_id=? OR passport=?",
                                         (sid, passport)).fetchone()
                    if exist:
                        conn.execute("""
                            UPDATE pilgrims SET name=?, visa=?, days_in_kingdom=?, status=?, agent=?, system_name=?,
                            entry_date=?, updated_at=CURRENT_TIMESTAMP WHERE system_id=?
                        """, (
                            row.get('name', row.get('اسم المعتمر', '')),
                            row.get('visa', row.get('رقم التأشيرة', '')),
                            int(row.get('days_in_kingdom', row.get('عدد الايام', 0))),
                            row.get('status', row.get('الحالة', 'داخل المملكة')),
                            row.get('agent', row.get('الوكيل', 'غير مسجل')),
                            row.get('system_name', row.get('اسم النظام', '')),
                            str(row.get('entry_date', row.get('تاريخ الدخول', ''))),
                            exist[0]
                        ))
                        updated += 1
                    else:
                        not_found += 1
                    progress.progress((i+1)/len(combined))
                conn.commit()
                st.success(f"تم تحديث {updated} | غير موجود {not_found}")

# ================== صفحة إرسال واتساب ==================
def whatsapp_page():
    st.header("📨 إرسال تقارير عبر واتساب")
    instance = st.text_input("UltraMsg instance ID", type="password")
    token = st.text_input("Token", type="password")
    conn = get_conn()
    agents = pd.read_sql_query("SELECT * FROM agents WHERE is_active=1 AND group_id!=''", conn)
    if not agents.empty:
        selected_agent = st.selectbox("اختر الوكيل", agents['name'].tolist())
        if selected_agent:
            agent_row = agents[agents['name'] == selected_agent].iloc[0]
            group_id = agent_row['group_id']
            st.write(f"معرف المجموعة: {group_id}")

            # إنشاء تقرير Excel مؤقت
            pilgrims = pd.read_sql_query("SELECT * FROM pilgrims WHERE agent=? AND status='داخل المملكة'",
                                         conn, params=(selected_agent,))
            if st.button("إرسال تقرير Excel"):
                if not instance or not token:
                    st.error("أدخل بيانات UltraMsg")
                else:
                    # إنشاء Excel في الذاكرة
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        pilgrims.to_excel(writer, index=False)
                    output.seek(0)

                    url = f"https://api.ultramsg.com/{instance}/messages/document"
                    files = {'file': (f"تقرير_{selected_agent}.xlsx", output, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                    data = {'token': token, 'to': group_id, 'caption': f"تقرير {selected_agent}"}
                    try:
                        resp = requests.post(url, data=data, files=files)
                        if resp.status_code == 200:
                            st.success("تم الإرسال بنجاح")
                        else:
                            st.error(f"فشل: {resp.text}")
                    except Exception as e:
                        st.error(str(e))

# ================== القائمة الرئيسية ==================
pages = {
    "🏠 الرئيسية": home,
    "👥 المعتمرين": pilgrims_page,
    "👔 الوكلاء": agents_page,
    "⚙️ المعالجة": processing_page,
    "📨 إرسال واتساب": whatsapp_page
}

st.sidebar.title("🕋 نظام متابعة المعتمرين")
st.sidebar.markdown("---")
choice = st.sidebar.radio("القائمة", list(pages.keys()))

pages[choice]()
