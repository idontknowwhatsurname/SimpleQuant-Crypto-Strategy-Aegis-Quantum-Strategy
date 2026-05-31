"""Gate.io 交易所实现"""
import os
import time
import hashlib
import hmac
import json
import urllib.request
import urllib.error
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from .base import ExchangeBase


class GateExchange(ExchangeBase):
    """Gate.io 交易所"""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.name = "gate"
        self.api_key = config.get('api_key', '') if config else os.environ.get('GATE_API_KEY', '')
        self.secret = config.get('secret', '') if config else os.environ.get('GATE_SECRET', '')
        self.base_url = 'https://api.gateio.ws/api/v4'
        self.headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}

    def get_name(self) -> str:
        return "Gate.io"

    def _public_get(self, path: str) -> dict:
        req = urllib.request.Request(self.base_url + path, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {'code': '-1', 'msg': str(e)}

    def _sign(self, method: str, path: str, query: str = '', body: str = '') -> dict:
        if not self.api_key:
            return {}
        t = str(int(time.time()))
        message = method + '\n' + path + '\n' + query + '\n' + body + '\n' + t
        signature = hmac.new(self.secret.encode(), message.encode(), hashlib.sha512).hexdigest()
        return {'KEY': self.api_key, 'Timestamp': t, 'SIGN': signature, 'Content-Type': 'application/json'}

    def _convert_symbol(self, symbol: str) -> str:
        return symbol.replace('-USDT-SWAP', '_USDT').replace('-SWAP', '').replace('-', '_')

    def _to_usdt(self, symbol: str) -> str:
        return symbol.replace('-USDT-SWAP', '').replace('-SWAP', '') + '_USDT'

    def fetch_ohlcv(self, symbol: str, timeframe: str = '4H',
                    limit: int = 100) -> pd.DataFrame:
        s = self._convert_symbol(symbol)
        result = self._public_get(f'/futures/usdt/candlesticks?contract={s}&interval={timeframe}&limit={limit}')
        if isinstance(result, list):
            candles = []
            for c in result:
                candles.append({
                    'timestamp': pd.to_datetime(int(c[0]), unit='s', utc=True),
                    'open': float(c[3]), 'high': float(c[5]),
                    'low': float(c[4]), 'close': float(c[2]),
                    'volume': float(c[1]),
                })
            df = pd.DataFrame(candles).set_index('timestamp')
            if len(df) > 14:
                df['returns'] = df['close'].pct_change()
                tr = pd.concat([abs(df['high']-df['low']),
                                abs(df['high']-df['close'].shift(1)),
                                abs(df['low']-df['close'].shift(1))], axis=1).max(axis=1)
                df['atr_14'] = tr.rolling(14).mean()
                df['high_20d'] = df['high'].rolling(20).max()
                df['dd_from_20d_high'] = (df['close'] - df['high_20d']) / df['high_20d']
                df['ret_24h'] = df['close'].pct_change(1)
            return df
        return pd.DataFrame()

    def fetch_ticker(self, symbol: str) -> dict:
        s = self._to_usdt(symbol)
        result = self._public_get(f'/spot/tickers?currency_pair={s}')
        if isinstance(result, list) and result:
            d = result[0]
            return {'symbol': symbol, 'price': float(d.get('last', 0)),
                    'volume_24h': float(d.get('quote_volume', 0)),
                    'high_24h': float(d.get('high_24h', 0)),
                    'low_24h': float(d.get('low_24h', 0)),
                    'change_24h': float(d.get('change_percentage', 0))}
        return {'symbol': symbol, 'price': 0}

    def fetch_funding_rate(self, symbol: str) -> float:
        s = self._convert_symbol(symbol)
        result = self._public_get(f'/futures/usdt/contracts/{s}')
        if isinstance(result, dict):
            return float(result.get('funding_rate', 0))
        return 0.0

    def fetch_open_interest(self, symbol: str) -> float:
        s = self._convert_symbol(symbol)
        result = self._public_get(f'/futures/usdt/contracts/{s}')
        if isinstance(result, dict):
            return float(result.get('openinterest', 0))
        return 0.0

    def place_order(self, symbol: str, side: str, size: float,
                    order_type: str = 'market', price: float = None,
                    lever: int = 1, reduce_only: bool = False) -> dict:
        s = self._convert_symbol(symbol)
        settle = 'usdt'
        body = {'contract': s, 'size': int(size * lever), 'side': side,
                'order_type': order_type}
        if price and order_type == 'limit':
            body['price'] = str(price)
        if reduce_only:
            body['reduce_only'] = True
        path = f'/futures/{settle}/orders'
        sign_headers = self._sign('POST', path, '', json.dumps(body))
        if not sign_headers:
            return {'success': False, 'error': 'API key not configured'}
        headers = {**self.headers, **sign_headers}
        data = json.dumps(body).encode()
        req = urllib.request.Request(self.base_url + path, data=data, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode())
                return {'success': True, 'order_id': result.get('id'),
                        'fill_price': result.get('fill_price', '0')}
        except urllib.error.HTTPError as e:
            return {'success': False, 'error': str(e)}

    def cancel_order(self, symbol: str, order_id: str) -> dict:
        s = self._convert_symbol(symbol)
        sign_headers = self._sign('DELETE', f'/futures/usdt/orders/{order_id}', '', '')
        headers = {**self.headers, **sign_headers} if sign_headers else self.headers
        req = urllib.request.Request(self.base_url + f'/futures/usdt/orders/{order_id}',
                                     headers=headers, method='DELETE')
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_positions(self, symbol: str = None) -> List[dict]:
        result = self._public_get('/futures/usdt/positions')
        positions = []
        if isinstance(result, list):
            for p in result:
                pos_amt = float(p.get('size', 0))
                if pos_amt == 0:
                    continue
                positions.append({
                    'exchange': 'Gate.io', 'symbol': p.get('contract', ''),
                    'position': pos_amt,
                    'avg_price': float(p.get('entry_price', 0)),
                    'mark_price': float(p.get('mark_price', 0)),
                    'unrealized_pnl': float(p.get('unrealised_pnl', 0)),
                    'leverage': int(float(p.get('leverage', 1))),
                    'liquidation_price': float(p.get('liquidation_price', 0)) if p.get('liquidation_price') else None,
                    'margin': float(p.get('im', 0)),
                })
        return positions

    def get_balance(self, ccy: str = 'USDT') -> float:
        acct = self._public_get('/wallet/total_balance')
        if isinstance(acct, dict):
            return float(acct.get('total', {}).get('amount', '0'))
        return 0.0

    def get_account_summary(self) -> dict:
        summary = {'exchange': 'Gate.io', 'total_equity': 0, 'available': 0,
                   'margin_used': 0, 'positions': [], 'timestamp': str(datetime.now())}
        acct = self._public_get('/futures/usdt/accounts')
        if isinstance(acct, dict):
            summary['total_equity'] = float(acct.get('total', 0))
            summary['available'] = float(acct.get('available', 0))
        summary['positions'] = self.get_positions()
        summary['margin_used'] = float(acct.get('position_margin', 0)) if isinstance(acct, dict) else 0
        summary['margin_ratio'] = (summary['margin_used'] / summary['total_equity']
                                    if summary['total_equity'] > 0 else 0)
        return summary

    def download_historical_data(self, symbol: str, start_date: str,
                                 end_date: str) -> pd.DataFrame:
        import ccxt
        ex = ccxt.gate({'enableRateLimit': True})
        since = ex.parse8601(start_date.replace('-', '') + 'T00:00:00Z')
        s = self._convert_symbol(symbol) + ':USDT'
        all_ohlcv = []
        while since < ex.milliseconds():
            batch = ex.fetch_ohlcv(s, '1d', since=since, limit=100)
            if not batch:
                break
            all_ohlcv.extend(batch)
            since = batch[-1][0] + 1
            time.sleep(0.15)
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        return df.set_index('timestamp').drop_duplicates()
