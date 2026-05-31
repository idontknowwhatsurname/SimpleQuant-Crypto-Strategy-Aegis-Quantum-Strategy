"""Discord 通知渠道"""
import os
import json
import urllib.request


class DiscordChannel:
    """Discord Webhook"""

    def __init__(self, config: dict = None):
        config = config or {}
        self.webhook = config.get('webhook_url', '') or os.environ.get('DISCORD_WEBHOOK', '')

    def send(self, message: str) -> dict:
        if not self.webhook:
            return {'success': False, 'error': '未配置 webhook_url'}
        data = json.dumps({'content': message[:2000]}).encode()
        req = urllib.request.Request(self.webhook, data=data,
                                     headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return {'success': resp.status == 204}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_report(self, text: str, title: str = None) -> dict:
        msg = f"**📊 {title or '交易报告'}**\n\n{text}" if title else f"**📊 交易报告**\n\n{text}"
        return self.send(msg)

    def send_alert(self, text: str, title: str = None) -> dict:
        msg = f"**🚨 {title or '风险告警'}**\n\n{text}" if title else f"**🚨 风险告警**\n\n{text}"
        return self.send(msg)
