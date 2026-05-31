"""Telegram 通知渠道"""
import os
import json
import urllib.request
import urllib.error


class TelegramChannel:
    """Telegram 通知"""

    def __init__(self, config: dict = None):
        config = config or {}
        self.bot_token = config.get('bot_token', '') or os.environ.get('TG_TOKEN', '')
        self.chat_id = config.get('chat_id', '') or os.environ.get('TG_CHAT', '')
        self.base_url = f'https://api.telegram.org/bot{self.bot_token}'

    def send(self, message: str) -> dict:
        if not self.bot_token or not self.chat_id:
            return {'success': False, 'error': '未配置'}
        url = f'{self.base_url}/sendMessage'
        data = json.dumps({'chat_id': self.chat_id, 'text': message, 'parse_mode': 'HTML'}).encode()
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                return {'success': result.get('ok', False)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_report(self, text: str, title: str = None) -> dict:
        msg = f"📊 {title or '交易报告'}\n\n{text}" if title else text
        return self.send(msg)

    def send_alert(self, text: str, title: str = None) -> dict:
        msg = f"🚨 {title or '风险告警'}\n\n{text}" if title else text
        return self.send(msg)
