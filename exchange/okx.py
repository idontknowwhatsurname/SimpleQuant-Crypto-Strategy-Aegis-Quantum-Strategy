"""OKX 交易所实现"""
import os
import time
import hmac
import hashlib
import base64
import json
import urllib.request
import urllib.error
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from .base import ExchangeBase


class OKXExchange(ExchangeBase):
    """OKX 交易所"""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.name = "okx"
        self.api_key = config.get('api_key', '') if config else os.environ.get('OKX_API_KEY', '')
        self.secret = config.get('secret', '') if config else os.environ.get('OKX_SECRET', '')
        self.passphrase = config.get('passphrase', '') if config else os.environ.get('OKX_PASSPHRASE', '')
        self.base_url = 'https://www.okx.com'
        self.demo = config.get('demo', False) if config else False
        self.public_headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}

    def get_name(self) -> str:
        return "OKX"

    def _sign(self, ts: str, method: str, path: str, body: str = '') -> str:
        msg = ts + method + path + body
        mac = hmac.new(self.secret.encode(), msg.encode(), hashlib.sha256)
        return base64.b64encode(mac.digest()).decode()

    def _public_get(self, path: str) -> dict:
        url = self.base_url + path
        req = urllib.request.Request(url, headers=self.public_headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {'code': '-1', 'msg': str(e)}

    def _private_request(self, method: str, path: str, body: dict = None) -> dict:
        if not self.api_key:
            return {'code': '-1', 'msg': 'API key not configured'}
        ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        body_str = json.dumps(body) if body else ''
        sign = self._sign(ts, method, path, body_str)
        url = self.base_url + path
        headers = {
            'OK-ACCESS-KEY': self.api_key, 'OK-ACCESS-SIGN': sign,
            'OK-ACCESS-TIMESTAMP': ts, 'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json',
        }
        if self.demo:
            headers['x-simulated-trading'] = '1'
        data = body_str.encode() if body_str else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return {'code': str(e.code), 'msg': str(e)}
        except Exception as e:
            return {'code': '-1', 'msg': str(e)}

    def fetch_ohlcv(self, symbol: str, timeframe: str = '4H',
                    limit: int = 100) -> pd.DataFrame:
        path = f'/api/v5/market/candles?instId={symbol}&bar={timeframe}&limit={limit}'
        result = self._public_get(path)
        if 'data' not in result:
            return pd.DataFrame()
        candles = []
        for c in reversed(result['data']):
            candles.append({
                'timestamp': pd.to_datetime(int(c[0]), unit='ms', utc=True),
                'open': float(c[1]), 'high': float(c[2]),
                'low': float(c[3]), 'close': float(c[4]),
                'volume': float(c[5]),
            })
        df = pd.DataFrame(candles).set_index('timestamp')
        df['returns'] = df['close'].pct_change()
        tr = pd.concat([df['high']-df['low'],
                        (df['high']-df['close'].shift(1)).abs(),
                        (df['low']-df['close'].shift(1)).abs()], axis=1).max(axis=1)
        df['atr_14'] = tr.rolling(14).mean()
        df['high_20d'] = df['high'].rolling(20).max()
        df['dd_from_20d_high'] = (df['close'] - df['high_20d']) / df['high_20d']
        df['ret_24h'] = df['close'].pct_change(1)
        return df.dropna()

    def fetch_ticker(self, symbol: str) -> dict:
        result = self._public_get(f'/api/v5/market/ticker?instId={symbol}')
        if 'data' in result and result['data']:
            d = result['data'][0]
            return {
                'symbol': symbol, 'price': float(d.get('last', 0)),
                'bid': float(d.get('bidPx', 0)), 'ask': float(d.get('askPx', 0)),
                'volume_24h': float(d.get('volCcy24h', 0)),
                'high_24h': float(d.get('high24h', 0)), 'low_24h': float(d.get('low24h', 0)),
                'change_24h': float(d.get('change24h', 0)),
            }
        return {'symbol': symbol, 'price': 0}

    def fetch_funding_rate(self, symbol: str) -> float:
        result = self._public_get(f'/api/v5/public/funding-rate?instId={symbol}')
        if 'data' in result and result['data']:
            return float(result['data'][0].get('fundingRate', 0))
        return 0.0

    def fetch_open_interest(self, symbol: str) -> float:
        result = self._public_get(f'/api/v5/public/open-interest?instId={symbol}')
        if 'data' in result and result['data']:
            return float(result['data'][0].get('oi', 0))
        return 0.0

    def place_order(self, symbol: str, side: str, size: float,
                    order_type: str = 'market', price: float = None,
                    lever: int = 1, reduce_only: bool = False) -> dict:
        ord_type_map = {'market': 'market', 'limit': 'limit', 'post_only': 'post_only'}
        body = {
            'instId': symbol, 'tdMode': 'cross',
            'side': side, 'ordType': ord_type_map.get(order_type, 'market'),
            'sz': str(size), 'lever': str(lever),
        }
        if price and order_type != 'market':
            body['px'] = str(price)
        if reduce_only:
            body['reduceOnly'] = 'true'
        result = self._private_request('POST', '/api/v5/trade/order', body)
        if result.get('code') == '0':
            d = result.get('data', [{}])[0]
            return {'success': True, 'order_id': d.get('ordId'), 'fill_price': d.get('fillPx')}
        return {'success': False, 'error': result.get('msg'), 'code': result.get('code')}

    def cancel_order(self, symbol: str, order_id: str) -> dict:
        result = self._private_request('POST', '/api/v5/trade/cancel-order',
                                       {'instId': symbol, 'ordId': order_id})
        return {'success': result.get('code') == '0'}

    def get_positions(self, symbol: str = None) -> List[dict]:
        path = '/api/v5/account/positions'
        if symbol:
            path += f'?instId={symbol}'
        result = self._private_request('GET', path)
        positions = []
        for p in result.get('data', []):
            if float(p.get('pos', 0)) == 0:
                continue
            positions.append({
                'exchange': 'OKX', 'symbol': p.get('instId'),
                'position': float(p.get('pos', 0)),
                'avg_price': float(p.get('avgPx', 0)),
                'mark_price': float(p.get('markPx', 0)),
                'unrealized_pnl': float(p.get('upl', 0)),
                'upl_ratio': float(p.get('uplRatio', 0)),
                'leverage': int(float(p.get('lever', 1))),
                'liquidation_price': float(p.get('liqPx', 0)) if p.get('liqPx') else None,
                'margin': float(p.get('margin', 0)),
                'margin_ratio': float(p.get('mgnRatio', 0)) if p.get('mgnRatio') else None,
            })
        return positions

    def get_balance(self, ccy: str = 'USDT') -> float:
        result = self._private_request('GET', '/api/v5/account/balance')
        if 'data' in result and result['data']:
            for d in result['data'][0].get('details', []):
                if d.get('ccy') == ccy:
                    return float(d.get('availBal', 0))
        return 0.0

    def get_account_summary(self) -> dict:
        result = self._private_request('GET', '/api/v5/account/balance')
        summary = {'exchange': 'OKX', 'total_equity': 0, 'available': 0,
                   'margin_used': 0, 'positions': [], 'timestamp': str(datetime.now())}
        if 'data' in result and result['data']:
            acct = result['data'][0]
            summary['total_equity'] = float(acct.get('totalEq', 0))
            for d in acct.get('details', []):
                if d.get('ccy') == 'USDT':
                    summary['available'] = float(d.get('availBal', 0))
                    summary['frozen'] = float(d.get('frozenBal', 0))
        summary['positions'] = self.get_positions()
        summary['margin_used'] = sum(p.get('margin', 0) for p in summary['positions'])
        summary['margin_ratio'] = (summary['margin_used'] / summary['total_equity']
                                    if summary['total_equity'] > 0 else 0)
        return summary

    def download_historical_data(self, symbol: str, start_date: str,
                                 end_date: str) -> pd.DataFrame:
        import ccxt
        ex = ccxt.okx({'enableRateLimit': True})
        since = ex.parse8601(start_date.replace('-', '') + 'T00:00:00Z')
        all_ohlcv = []
        while since < ex.milliseconds():
            batch = ex.fetch_ohlcv(symbol, '1d', since=since, limit=100)
            if not batch:
                break
            all_ohlcv.extend(batch)
            since = batch[-1][0] + 1
            time.sleep(0.15)
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        return df.set_index('timestamp').drop_duplicates()
