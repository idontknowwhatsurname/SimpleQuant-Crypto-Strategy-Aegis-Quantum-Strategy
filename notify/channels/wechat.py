"""企业微信通知渠道"""
import os
import json
import urllib.request


class WeChatChannel:
    """企业微信 Webhook"""

    def __init__(self, config: dict = None):
        config = config or {}
        self.webhook = config.get('webhook_url', '') or os.environ.get('WECHAT_WEBHOOK', '')

    def send(self, message: str) -> dict:
        if not self.webhook:
            return {'success': False, 'error': '未配置 webhook_url'}
        data = json.dumps({'msgtype': 'text', 'text': {'content': message}}).encode()
        req = urllib.request.Request(self.webhook, data=data, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                r = json.loads(resp.read().decode())
                return {'success': r.get('errcode', -1) == 0}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_report(self, text: str, title: str = None) -> dict:
        msg = f"📊 {title}\n\n{text}" if title else text
        return self.send(msg)

    def send_alert(self, text: str, title: str = None) -> dict:
        msg = f"🚨 {title}\n\n{text}" if title else text
        return self.send(msg)
