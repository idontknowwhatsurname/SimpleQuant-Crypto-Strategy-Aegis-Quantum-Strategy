"""
下单执行器 - 通过 OKX API 执行交易指令
支持市价单/限价单/条件单/止损单
"""
import os
import time
import hmac
import hashlib
import base64
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class OrderExecutor:
    """
    OKX 订单执行器

    用法:
        executor = OrderExecutor()
        result = executor.place_market_order("BTC-USDT-SWAP", "buy", 0.01)
    """

    def __init__(self, api_key: str = None, secret: str = None,
                 passphrase: str = None, demo: bool = False):
        self.api_key = api_key or os.environ.get('OKX_API_KEY', '')
        self.secret = secret or os.environ.get('OKX_SECRET', '')
        self.passphrase = passphrase or os.environ.get('OKX_PASSPHRASE', '')
        self.base_url = 'https://www.okx.com'
        self.demo = demo

    def _sign(self, timestamp: str, method: str, path: str, body: str = '') -> str:
        message = timestamp + method + path + body
        mac = hmac.new(self.secret.encode(), message.encode(), hashlib.sha256)
        return base64.b64encode(mac.digest()).decode()

    def _request(self, method: str, path: str, body: dict = None) -> dict:
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        body_str = json.dumps(body) if body else ''
        sign = self._sign(timestamp, method, path, body_str)

        url = self.base_url + path
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': sign,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json',
        }

        if self.demo:
            headers['x-simulated-trading'] = '1'

        data = body_str.encode() if body_str else None
        import urllib.request
        import urllib.error
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return {'code': str(e.code), 'msg': str(e)}
        except Exception as e:
            return {'code': '-1', 'msg': str(e)}

    def place_market_order(self, inst_id: str, side: str, size: float,
                           lever: int = 1, reduce_only: bool = False) -> dict:
        """
        市价单

        Args:
            inst_id: 产品 ID, e.g. BTC-USDT-SWAP
            side: buy / sell
            size: 数量
            lever: 杠杆倍数
            reduce_only: 是否只减仓
        """
        body = {
            'instId': inst_id,
            'tdMode': 'cross',
            'side': side,
            'ordType': 'market',
            'sz': str(size),
            'lever': str(lever),
        }
        if reduce_only:
            body['reduceOnly'] = 'true'

        result = self._request('POST', '/api/v5/trade/order', body)

        if result.get('code') == '0':
            data = result.get('data', [{}])[0]
            return {
                'success': True,
                'order_id': data.get('ordId'),
                'state': data.get('state'),
                'fill_price': data.get('fillPx', 'N/A'),
                'fill_size': data.get('fillSz', 'N/A'),
            }
        else:
            return {
                'success': False,
                'error': result.get('msg', 'Unknown error'),
                'code': result.get('code'),
            }

    def place_limit_order(self, inst_id: str, side: str, size: float,
                          price: float, lever: int = 1,
                          post_only: bool = True) -> dict:
        """
        限价单

        Args:
            inst_id: 产品 ID
            side: buy / sell
            size: 数量
            price: 价格
            lever: 杠杆倍数
            post_only: 是否只做 maker
        """
        body = {
            'instId': inst_id,
            'tdMode': 'cross',
            'side': side,
            'ordType': 'post_only' if post_only else 'limit',
            'sz': str(size),
            'px': str(price),
            'lever': str(lever),
        }
        result = self._request('POST', '/api/v5/trade/order', body)

        if result.get('code') == '0':
            data = result.get('data', [{}])[0]
            return {
                'success': True,
                'order_id': data.get('ordId'),
                'state': data.get('state'),
            }
        else:
            return {'success': False, 'error': result.get('msg'), 'code': result.get('code')}

    def place_stop_order(self, inst_id: str, side: str, size: float,
                         trigger_price: float, order_price: float = None,
                         lever: int = 1) -> dict:
        """
        条件止损单

        Args:
            inst_id: 产品 ID
            side: buy / sell
            size: 数量
            trigger_price: 触发价格
            order_price: 委托价格 (默认市价)
            lever: 杠杆倍数
        """
        body = {
            'instId': inst_id,
            'tdMode': 'cross',
            'side': side,
            'ordType': 'conditional',
            'sz': str(size),
            'triggerPx': str(trigger_price),
            'lever': str(lever),
        }
        if order_price:
            body['px'] = str(order_price)
        else:
            body['ordType'] = 'move_order_stop'

        result = self._request('POST', '/api/v5/trade/order-algo', body)

        if result.get('code') == '0':
            data = result.get('data', [{}])[0]
            return {
                'success': True,
                'algo_id': data.get('algoId'),
                'state': data.get('state'),
            }
        else:
            return {'success': False, 'error': result.get('msg'), 'code': result.get('code')}

    def cancel_order(self, inst_id: str, order_id: str) -> dict:
        """撤销订单"""
        body = {'instId': inst_id, 'ordId': order_id}
        result = self._request('POST', '/api/v5/trade/cancel-order', body)
        return {'success': result.get('code') == '0', 'data': result}

    def get_positions(self, inst_id: str = None) -> list:
        """获取持仓"""
        path = '/api/v5/account/positions'
        if inst_id:
            path += f'?instId={inst_id}'
        result = self._request('GET', path)
        return result.get('data', [])

    def get_balance(self) -> float:
        """获取 USDT 余额"""
        result = self._request('GET', '/api/v5/account/balance')
        if 'data' in result and result['data']:
            for d in result['data'][0].get('details', []):
                if d.get('ccy') == 'USDT':
                    return float(d.get('availBal', 0))
        return 0.0

    def set_leverage(self, inst_id: str, lever: int,
                     mgn_mode: str = 'cross') -> dict:
        """设置杠杆"""
        body = {'instId': inst_id, 'lever': str(lever), 'mgnMode': mgn_mode}
        result = self._request('POST', '/api/v5/account/set-leverage', body)
        return {'success': result.get('code') == '0', 'data': result}
