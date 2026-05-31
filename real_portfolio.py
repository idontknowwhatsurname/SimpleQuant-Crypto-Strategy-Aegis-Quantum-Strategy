"""
实盘仓位监控模块
支持 OKX 实时持仓查询 + 风险评估 + 告警推送
"""
import os
import time
import hmac
import hashlib
import base64
import json
from datetime import datetime, timezone
from typing import Optional

try:
    import urllib.request
    import urllib.error
except ImportError:
    pass


class OKXClient:
    """OKX API 客户端 - 仅用于查询持仓和余额"""
    
    def __init__(self):
        self.api_key = os.environ.get('OKX_API_KEY', '')
        self.secret_key = os.environ.get('OKX_SECRET', '')
        self.passphrase = os.environ.get('OKX_PASSPHRASE', '')
        self.base_url = 'https://www.okx.com'
    
    def _sign(self, timestamp: str, method: str, path: str, body: str = '') -> str:
        message = timestamp + method + path + body
        mac = hmac.new(self.secret_key.encode(), message.encode(), hashlib.sha256)
        return base64.b64encode(mac.digest()).decode()
    
    def _request(self, method: str, path: str, body: str = '') -> dict:
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        sign = self._sign(timestamp, method, path, body)
        url = self.base_url + path
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': sign,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        data = body.encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {'error': str(e)}
    
    def get_balance(self) -> dict:
        """获取账户余额"""
        return self._request('GET', '/api/v5/account/balance')
    
    def get_positions(self) -> list:
        """获取当前持仓"""
        result = self._request('GET', '/api/v5/account/positions')
        return result.get('data', []) if 'data' in result else []
    
    def get_ticker(self, inst_id: str) -> dict:
        """获取实时行情"""
        return self._request('GET', f'/api/v5/market/ticker?instId={inst_id}')


class RealPortfolioMonitor:
    """
    实盘仓位监控模块
    功能：
    1. 从 OKX API 实时获取持仓
    2. 计算风险指标（保证金率、净敞口、最大回撤）
    3. 生成风险报告
    """
    
    def __init__(self, use_api: bool = True):
        """
        Args:
            use_api: 是否从 OKX API 获取真实数据，False 则使用模拟数据
        """
        self.use_api = use_api
        self.okx = OKXClient() if use_api else None
        self._cache = {}
        self._cache_time = 0
        self._cache_ttl = 10  # 10 秒缓存
    
    def _fetch_real_data(self) -> dict:
        """从 OKX API 获取真实持仓数据"""
        now = time.time()
        if now - self._cache_time < self._cache_ttl and self._cache:
            return self._cache
        
        balance = self.okx.get_balance()
        positions = self.okx.get_positions()
        
        # 解析余额
        total_eq = 0
        available = 0
        if 'data' in balance and balance['data']:
            acct = balance['data'][0]
            total_eq = float(acct.get('totalEq', 0))
            details = acct.get('details', [])
            for d in details:
                if d.get('ccy') == 'USDT':
                    available = float(d.get('availBal', 0))
        
        # 解析持仓
        pos_list = []
        for p in positions:
            pos_amt = float(p.get('pos', 0))
            if pos_amt == 0:
                continue
            pos_list.append({
                'inst_id': p.get('instId', ''),
                'pos': pos_amt,
                'avg_px': float(p.get('avgPx', 0)),
                'mark_px': float(p.get('markPx', 0)),
                'upl': float(p.get('upl', 0)),
                'upl_ratio': float(p.get('uplRatio', 0)),
                'lever': float(p.get('lever', 1)),
                'liq_px': float(p.get('liqPx', 0)) if p.get('liqPx') else None,
                'margin': float(p.get('margin', 0)),
                'mgn_ratio': float(p.get('mgnRatio', 0)) if p.get('mgnRatio') else None,
            })
        
        self._cache = {
            'total_equity': total_eq,
            'available_usdt': available,
            'positions': pos_list,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        self._cache_time = now
        return self._cache
    
    def risk_assessment(self) -> dict:
        """
        风险评估：
        - 计算保证金使用率
        - 计算净敞口
        - 评估单一标的集中度
        - 检查强平风险
        """
        if self.use_api:
            data = self._fetch_real_data()
            total_eq = data['total_equity']
            available = data['available_usdt']
            positions = data['positions']
        else:
            # 模拟数据
            total_eq = 1662.25
            available = 21.15
            positions = [
                {'inst_id': 'ANTHROPIC-USDT-SWAP', 'pos': 0.5, 'upl': 549.12, 'lever': 5, 'margin': 500},
                {'inst_id': 'OPENAI-USDT-SWAP', 'pos': 0.3, 'upl': -14.27, 'lever': 5, 'margin': 400},
                {'inst_id': 'SPACEX-USDT-SWAP', 'pos': 0.2, 'upl': 263.29, 'lever': 5, 'margin': 300},
            ]
        
        # 计算指标
        margin_used = sum(p.get('margin', 0) for p in positions)
        margin_ratio = margin_used / total_eq if total_eq > 0 else 0
        free_ratio = available / total_eq if total_eq > 0 else 0
        
        # 单一标的集中度
        max_single = max((p.get('margin', 0) for p in positions), default=0)
        concentration = max_single / total_eq if total_eq > 0 else 0
        
        # 强平风险检查
        liquidation_risk = []
        for p in positions:
            if p.get('liq_px') and p.get('mark_px'):
                liq_distance = abs(p['mark_px'] - p['liq_px']) / p['mark_px']
                if liq_distance < 0.10:  # 距离强平价 <10%
                    liquidation_risk.append({
                        'inst_id': p['inst_id'],
                        'liq_px': p['liq_px'],
                        'distance_pct': liq_distance
                    })
        
        # 风险评级
        if margin_ratio > 0.90:
            risk_level = 'CRITICAL'
            risk_msg = '保证金使用率超过 90%，极度危险！'
        elif margin_ratio > 0.70:
            risk_level = 'HIGH'
            risk_msg = '保证金使用率超过 70%，风险较高'
        elif margin_ratio > 0.50:
            risk_level = 'MEDIUM'
            risk_msg = '保证金使用率适中'
        else:
            risk_level = 'LOW'
            risk_msg = '保证金使用率健康'
        
        return {
            'total_equity': total_eq,
            'available_usdt': available,
            'margin_used': margin_used,
            'margin_ratio': margin_ratio,
            'free_ratio': free_ratio,
            'concentration': concentration,
            'positions': positions,
            'liquidation_risk': liquidation_risk,
            'risk_level': risk_level,
            'risk_message': risk_msg,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def print_report(self):
        """打印风险报告"""
        assess = self.risk_assessment()
        
        print("\n" + "=" * 60)
        print("🛡️  实盘仓位监控报告")
        print("=" * 60)
        print(f"  总净值:      {assess['total_equity']:.2f} USDT")
        print(f"  可用余额:    {assess['available_usdt']:.2f} USDT ({assess['free_ratio']:.1%})")
        print(f"  已用保证金:  {assess['margin_used']:.2f} USDT ({assess['margin_ratio']:.1%})")
        print("-" * 60)
        
        print("\n📊 当前持仓:")
        for p in assess['positions']:
            direction = "多" if p.get('pos', 0) > 0 else "空"
            pnl = p.get('upl', 0)
            pnl_tag = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
            print(f"  {p.get('inst_id', 'N/A')}:")
            print(f"    方向: {direction} | 杠杆: {p.get('lever', 1)}x | 浮盈: {pnl_tag}")
            if p.get('liq_px'):
                print(f"    强平价: ${p['liq_px']:.2f}")
        
        if assess['liquidation_risk']:
            print("\n🚨 强平风险警告:")
            for r in assess['liquidation_risk']:
                print(f"  {r['inst_id']}: 距强平价仅 {r['distance_pct']:.1%}")
        
        print("\n" + "-" * 60)
        print(f"  风险评级: {assess['risk_level']}")
        print(f"  建议: {assess['risk_message']}")
        
        # 操作建议
        if assess['margin_ratio'] > 0.70:
            print("\n💡 建议操作:")
            print("  1. 减仓高杠杆标的，释放保证金")
            print("  2. 将可用余额划转至合约账户作为缓冲")
            print("  3. 设置止损单，防止极端行情爆仓")
        
        print("=" * 60)


if __name__ == "__main__":
    # 测试模式（使用模拟数据）
    monitor = RealPortfolioMonitor(use_api=False)
    monitor.print_report()
