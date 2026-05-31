"""QQ 通知渠道 - 通过 QQ Bot API / 第三方桥接"""
import os
import json
import urllib.request


class QQChannel:
    """QQ 通知 (通过 QQ Bot API 或 OneBot 协议)"""

    def __init__(self, config: dict = None):
        config = config or {}
        self.api_url = config.get('api_url', '') or os.environ.get('QQ_API_URL', '')
        self.user_id = config.get('user_id', '') or os.environ.get('QQ_USER_ID', '')
        self.token = config.get('token', '') or os.environ.get('QQ_TOKEN', '')

    def send(self, message: str) -> dict:
        if not self.api_url:
            return {'success': False, 'error': '未配置 QQ API URL'}
        # 支持 OneBot v11 和 v12 协议
        body = {
            'user_id': self.user_id,
            'message': message[:2000],
        }
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            f'{self.api_url.rstrip("/")}/send_private_msg',
            data=data, headers=headers
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_report(self, text: str, title: str = None) -> dict:
        msg = f"[交易报告] {title or ''}\n{text}" if title else f"[交易报告]\n{text}"
        return self.send(msg)

    def send_alert(self, text: str, title: str = None) -> dict:
        msg = f"[告警] {title or ''}\n{text}" if title else f"[告警]\n{text}"
        return self.send(msg)
