"""
通知模块 - 支持 Telegram / 企业微信 / 飞书
用于推送交易信号、风险告警、每日报告
"""
import os
import json
from typing import Optional
from datetime import datetime, timezone

try:
    import urllib.request
    import urllib.error
except ImportError:
    pass


class TelegramNotifier:
    """Telegram 通知推送"""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or os.environ.get('TG_TOKEN', '')
        self.chat_id = chat_id or os.environ.get('TG_CHAT', '')
        self.base_url = f'https://api.telegram.org/bot{self.bot_token}'
    
    def send(self, message: str, parse_mode: str = 'HTML') -> bool:
        """发送消息"""
        if not self.bot_token or not self.chat_id:
            print("[Telegram] 未配置 bot_token 或 chat_id")
            return False
        
        url = f'{self.base_url}/sendMessage'
        data = json.dumps({
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode
        }).encode()
        
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                return result.get('ok', False)
        except Exception as e:
            print(f"[Telegram] 发送失败: {e}")
            return False
    
    def send_signal(self, symbol: str, signal: str, price: float, reason: str):
        """发送交易信号"""
        emoji = "🟢" if signal == "long" else "🔴" if signal == "short" else "⚪"
        msg = f"""
{emoji} <b>交易信号</b>

<b>币种:</b> {symbol}
<b>信号:</b> {signal.upper()}
<b>价格:</b> ${price:,.2f}
<b>原因:</b> {reason}
<b>时间:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""
        return self.send(msg.strip())
    
    def send_risk_alert(self, alert_type: str, message: str, risk_level: str):
        """发送风险告警"""
        emoji = "🚨" if risk_level == "critical" else "⚠️" if risk_level == "warning" else "ℹ️"
        msg = f"""
{emoji} <b>风险告警</b>

<b>类型:</b> {alert_type}
<b>级别:</b> {risk_level.upper()}
<b>详情:</b> {message}
<b>时间:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""
        return self.send(msg.strip())
    
    def send_daily_report(self, report: dict):
        """发送每日报告"""
        msg = f"""
📊 <b>每日交易报告</b>

<b>日期:</b> {report.get('date', 'N/A')}
<b>总净值:</b> ${report.get('total_equity', 0):,.2f}
<b>日收益:</b> {report.get('daily_pnl', 0):.2%}
<b>持仓数:</b> {report.get('position_count', 0)}
<b>风险评级:</b> {report.get('risk_level', 'N/A')}

<b>当前持仓:</b>
{report.get('positions_text', '无持仓')}

<b>AI 建议:</b>
{report.get('ai_suggestion', '无')}
"""
        return self.send(msg.strip())


class WeChatNotifier:
    """企业微信 Webhook 推送"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.environ.get('WECHAT_WEBHOOK', '')
    
    def send(self, message: str) -> bool:
        """发送消息"""
        if not self.webhook_url:
            print("[WeChat] 未配置 webhook_url")
            return False
        
        data = json.dumps({
            'msgtype': 'text',
            'text': {'content': message}
        }).encode()
        
        req = urllib.request.Request(self.webhook_url, data=data, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                return result.get('errcode', -1) == 0
        except Exception as e:
            print(f"[WeChat] 发送失败: {e}")
            return False


class FeishuNotifier:
    """飞书 Webhook 推送"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.environ.get('FEISHU_WEBHOOK', '')
    
    def send(self, message: str) -> bool:
        """发送消息"""
        if not self.webhook_url:
            print("[Feishu] 未配置 webhook_url")
            return False
        
        data = json.dumps({
            'msg_type': 'text',
            'content': {'text': message}
        }).encode()
        
        req = urllib.request.Request(self.webhook_url, data=data, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                return result.get('code', -1) == 0
        except Exception as e:
            print(f"[Feishu] 发送失败: {e}")
            return False


class NotifyManager:
    """通知管理器 - 统一管理所有通知渠道"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.telegram = TelegramNotifier(
            bot_token=self.config.get('tg_token'),
            chat_id=self.config.get('tg_chat')
        )
        self.wechat = WeChatNotifier(
            webhook_url=self.config.get('wechat_webhook')
        )
        self.feishu = FeishuNotifier(
            webhook_url=self.config.get('feishu_webhook')
        )
    
    def notify(self, message: str, channels: list = None):
        """
        发送通知到指定渠道
        
        Args:
            message: 消息内容
            channels: 渠道列表，默认 ['telegram']
        """
        if channels is None:
            channels = ['telegram']
        
        results = {}
        for channel in channels:
            if channel == 'telegram':
                results['telegram'] = self.telegram.send(message)
            elif channel == 'wechat':
                results['wechat'] = self.wechat.send(message)
            elif channel == 'feishu':
                results['feishu'] = self.feishu.send(message)
        
        return results
    
    def send_signal(self, symbol: str, signal: str, price: float, reason: str,
                    channels: list = None):
        """发送交易信号"""
        emoji = "🟢" if signal == "long" else "🔴" if signal == "short" else "⚪"
        message = f"{emoji} {signal.upper()} {symbol} @ ${price:,.2f}\n原因: {reason}"
        return self.notify(message, channels)
    
    def send_risk_alert(self, alert_type: str, message: str, risk_level: str,
                        channels: list = None):
        """发送风险告警"""
        emoji = "🚨" if risk_level == "critical" else "⚠️"
        full_message = f"{emoji} [{risk_level.upper()}] {alert_type}\n{message}"
        return self.notify(full_message, channels)
