#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📱 مرسل واتساب عبر UltraMsg API"""

import requests
import time
from datetime import datetime
from typing import Dict, Any
import streamlit as st


class WhatsAppSender:
    def __init__(self, instance_id: str = "", token: str = ""):
        self.instance_id = instance_id
        self.token = token
        self.base_url = f"https://api.ultramsg.com/{self.instance_id}"
        self.delay = 3

    def is_configured(self) -> bool:
        return bool(self.instance_id and self.token)

    def _clean_group_id(self, group_id: str) -> str:
        group_id = str(group_id).strip()
        if group_id.isdigit():
            return f"{group_id}@g.us"
        return group_id

    def send_message(self, chat_id: str, message: str) -> Dict[str, Any]:
        if not self.is_configured():
            return {'success': False, 'error': 'غير مهيأ'}
        try:
            url = f"{self.base_url}/messages/chat"
            payload = {'token': self.token, 'to': self._clean_group_id(chat_id), 'body': message}
            response = requests.post(url, data=payload, timeout=30)
            if response.status_code == 200:
                return {'success': True}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_document(self, chat_id: str, file_path: str, caption: str = "", filename: str = None) -> Dict[str, Any]:
        if not self.is_configured():
            return {'success': False, 'error': 'غير مهيأ'}
        try:
            if not filename:
                filename = f"تقرير_{datetime.now().strftime('%H%M')}.pdf"

            url = f"{self.base_url}/messages/document"
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f)}
                data = {'token': self.token, 'to': self._clean_group_id(chat_id), 'caption': caption}
                response = requests.post(url, data=data, files=files, timeout=60)

            if response.status_code == 200:
                return {'success': True}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_report_to_agent(self, agent_name: str, group_id: str, file_path: str,
                            stats_count: int = 0, over_80_count: int = 0) -> Dict[str, Any]:
        today = datetime.now().strftime('%Y/%m/%d')
        caption = (
            f"📄 *تقرير متابعة المعتمرين اليومي*\n\n"
            f"📅 *التاريخ:* {today}\n"
            f"👤 *الوكيل:* {agent_name}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📈 *إجمالي المعتمرين:* ( {stats_count} )\n"
            f"🚨 *المتجاوزين 80 يوم:* ( {over_80_count} )\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ *الحالة:* تم التحديث بنجاح ✅"
        )
        return self.send_document(group_id, file_path, caption)

    def test_connection(self) -> bool:
        if not self.is_configured():
            return False
        try:
            url = f"{self.base_url}/instance/status"
            response = requests.get(url, params={'token': self.token}, timeout=10)
            return response.status_code == 200
        except:
            return False


# ==================== إعدادات افتراضية للمرسل ====================
def get_whatsapp_sender() -> WhatsAppSender:
    instance_id = st.secrets.get("ULTRAMSG_INSTANCE_ID", "")
    token = st.secrets.get("ULTRAMSG_TOKEN", "")
    return WhatsAppSender(instance_id, token)