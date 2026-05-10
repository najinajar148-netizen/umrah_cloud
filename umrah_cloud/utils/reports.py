#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📊 مولد التقارير - Streamlit Edition"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from fpdf import FPDF
import os
import tempfile


class ReportsGenerator:
    def __init__(self):
        self.output_dir = Path("output/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_agent_excel(self, df: pd.DataFrame, agent_name: str) -> str:
        safe_name = agent_name.replace('/', '-').replace('\\', '-')
        file_path = self.output_dir / f"تقرير_{safe_name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        columns = ['system_id', 'name', 'passport', 'visa', 'entry_date', 'days_in_kingdom', 'status']
        df_export = df[columns].copy()
        df_export.columns = ['رقم النظام', 'اسم المعتمر', 'رقم الجواز', 'رقم التأشيرة',
                             'تاريخ الدخول', 'عدد الأيام', 'الحالة']
        df_export.to_excel(file_path, index=False, engine='openpyxl')
        return str(file_path)

    def create_agent_pdf(self, df: pd.DataFrame, agent_name: str) -> str:
        safe_name = agent_name.replace('/', '-').replace('\\', '-')
        file_path = self.output_dir / f"تقرير_{safe_name}_{datetime.now().strftime('%Y%m%d')}.pdf"

        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()

        # إضافة خط عربي
        try:
            pdf.add_font('Arabic', '', 'Amiri-Regular.ttf', uni=True)
            pdf.add_font('Arabic', 'B', 'Amiri-Bold.ttf', uni=True)
            font_name = 'Arabic'
        except:
            font_name = 'Helvetica'

        # عنوان
        pdf.set_font(font_name, 'B', 18)
        pdf.cell(280, 15, 'تقرير متابعة المعتمرين', ln=True, align='C')
        pdf.set_font(font_name, '', 12)
        pdf.cell(280, 10, f'الوكيل: {agent_name}', ln=True, align='C')
        pdf.cell(280, 10, f'التاريخ: {datetime.now().strftime("%Y/%m/%d")}', ln=True, align='C')
        pdf.ln(10)

        # جدول
        columns = ['اسم المعتمر', 'رقم الجواز', 'رقم التأشيرة', 'تاريخ الدخول', 'عدد الأيام', 'الحالة']
        col_widths = [70, 45, 45, 40, 30, 40]

        # رأس الجدول
        pdf.set_font(font_name, 'B', 10)
        pdf.set_fill_color(0, 102, 204)
        pdf.set_text_color(255, 255, 255)
        for i, col in enumerate(columns):
            pdf.cell(col_widths[i], 10, col, border=1, fill=True, align='C')
        pdf.ln()

        # صفوف الجدول
        pdf.set_font(font_name, '', 9)
        pdf.set_text_color(0, 0, 0)
        for _, row in df.iterrows():
            fill = row.get('days_in_kingdom', 0) >= 80
            if fill:
                pdf.set_fill_color(255, 230, 230)

            values = [
                str(row.get('name', ''))[:30],
                str(row.get('passport', '')),
                str(row.get('visa', '')),
                str(row.get('entry_date', ''))[:10],
                str(row.get('days_in_kingdom', '')),
                str(row.get('status', ''))
            ]
            for i, val in enumerate(values):
                pdf.cell(col_widths[i], 8, val, border=1, fill=fill, align='C')
            pdf.ln()

        pdf.output(str(file_path))
        return str(file_path)

    def create_bulk_excel(self, df: pd.DataFrame, filename: str = "جميع_المعتمرين") -> str:
        file_path = self.output_dir / f"{filename}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df.to_excel(file_path, index=False, engine='openpyxl')
        return str(file_path)


def generate_report(df: pd.DataFrame, agent_name: str, format_type: str = 'PDF') -> str:
    generator = ReportsGenerator()
    if format_type.upper() == 'PDF':
        return generator.create_agent_pdf(df, agent_name)
    else:
        return generator.create_agent_excel(df, agent_name)