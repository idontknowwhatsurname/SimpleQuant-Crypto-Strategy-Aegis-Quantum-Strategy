"""通知模块 - 统一通知管理器 + 多通道支持"""
from .channels.telegram import TelegramChannel
from .channels.wechat import WeChatChannel
from .channels.discord import DiscordChannel
from .channels.qq import QQChannel
from .channels.email import EmailChannel


class NotifyManager:
    """
    统一通知管理器
    用户可自定义: 什么报告发到什么渠道，报告格式，提醒频率
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.channels = {}
        self._init_channels()

    def _init_channels(self):
        """初始化所有配置的渠道"""
        channel_map = {
            'telegram': TelegramChannel,
            'wechat': WeChatChannel,
            'discord': DiscordChannel,
            'qq': QQChannel,
            'email': EmailChannel,
        }
        channel_config = self.config.get('channels', {})
        for name, cls in channel_map.items():
            cfg = channel_config.get(name, {})
            if cfg.get('enabled', False) or name in self.config.get('enabled_channels', []):
                self.channels[name] = cls(cfg)

    def send(self, message: str, channels: list = None, 
             msg_type: str = 'text', title: str = None) -> dict:
        """
        发送消息到指定渠道

        Args:
            message: 消息内容
            channels: 渠道列表，默认所有已配置的渠道
            msg_type: 消息类型 'text'/'report'/'alert'/'signal'
            title: 消息标题
        """
        if channels is None:
            channels = list(self.channels.keys())
        results = {}
        for name in channels:
            channel = self.channels.get(name)
            if channel:
                try:
                    if msg_type == 'report':
                        results[name] = channel.send_report(message, title)
                    elif msg_type == 'alert':
                        results[name] = channel.send_alert(message, title)
                    else:
                        results[name] = channel.send(message)
                except Exception as e:
                    results[name] = {'success': False, 'error': str(e)}
        return results

    def send_report(self, report_text: str, title: str = None,
                    channels: list = None) -> dict:
        """发送报告"""
        return self.send(report_text, channels, msg_type='report', title=title)

    def send_alert(self, alert_text: str, title: str = None,
                   channels: list = None) -> dict:
        """发送告警"""
        return self.send(alert_text, channels, msg_type='alert', title=title)

    def send_signal(self, symbol: str, signal: str, price: float,
                    channels: list = None) -> dict:
        """发送交易信号"""
        emoji = "🟢" if signal in ('buy', 'long') else "🔴" if signal in ('sell', 'short') else "⚪"
        msg = f"{emoji} 交易信号: {symbol}\n方向: {signal.upper()}\n价格: ${price:,.2f}"
        return self.send(msg, channels, msg_type='signal')

    def add_channel(self, name: str, config: dict):
        """动态添加渠道"""
        channel_map = {
            'telegram': TelegramChannel,
            'wechat': WeChatChannel,
            'discord': DiscordChannel,
            'qq': QQChannel,
            'email': EmailChannel,
        }
        cls = channel_map.get(name)
        if cls:
            self.channels[name] = cls(config)

    def get_available_channels(self) -> list:
        """返回已配置的渠道列表"""
        return list(self.channels.keys())
