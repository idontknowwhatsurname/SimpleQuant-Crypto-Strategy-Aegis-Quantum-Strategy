"""Gmail 邮件通知渠道"""
import os
import json
import urllib.request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailChannel:
    """Gmail / SMTP 邮件"""

    def __init__(self, config: dict = None):
        config = config or {}
        self.smtp_host = config.get('smtp_host', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username', '') or os.environ.get('EMAIL_USERNAME', '')
        self.password = config.get('password', '') or os.environ.get('EMAIL_PASSWORD', '')
        self.from_addr = config.get('from', self.username)
        self.to_addrs = config.get('to', '') or os.environ.get('EMAIL_TO', '')
        self.use_tls = config.get('use_tls', True)

    def send(self, message: str) -> dict:
        if not self.username or not self.password or not self.to_addrs:
            return {'success': False, 'error': '邮件配置不完整'}
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_addr
            msg['To'] = self.to_addrs
            msg['Subject'] = 'Aegis Quantum Strategy - 通知'
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_report(self, text: str, title: str = None) -> dict:
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_addr
            msg['To'] = self.to_addrs
            msg['Subject'] = f"📊 {title or '交易报告'}"
            msg.attach(MIMEText(text, 'plain', 'utf-8'))
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_alert(self, text: str, title: str = None) -> dict:
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_addr
            msg['To'] = self.to_addrs
            msg['Subject'] = f"🚨 {title or '风险告警'}"
            msg.attach(MIMEText(text, 'plain', 'utf-8'))
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
