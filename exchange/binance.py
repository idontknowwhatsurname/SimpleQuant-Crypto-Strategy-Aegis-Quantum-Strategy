"""Binance 交易所实现"""
import os
import time
import hmac
import hashlib
import json
import urllib.request
import urllib.error
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from .base import ExchangeBase


class BinanceExchange(ExchangeBase):
    """Binance 交易所"""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.name = "binance"
        self.api_key = config.get('api_key', '') if config else os.environ.get('BINANCE_API_KEY', '')
        self.secret = config.get('secret', '') if config else os.environ.get('BINANCE_SECRET', '')
        self.base_url = 'https://api.binance.com'
        self.fapi_url = 'https://fapi.binance.com'
        self.testnet = config.get('testnet', False) if config else False
        self.headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}

    def get_name(self) -> str:
        return "Binance"

    def _public_get(self, base_url: str, path: str) -> dict:
        req = urllib.request.Request(base_url + path, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {'code': '-1', 'msg': str(e)}

    def _sign(self, params: dict) -> str:
        query = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
        signature = hmac.new(self.secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        return query + f'&signature={signature}'

    def _private_get(self, base_url: str, path: str, params: dict = None) -> dict:
        if not self.api_key:
            return {'code': '-1', 'msg': 'API key not configured'}
        params = params or {}
        params['timestamp'] = int(time.time() * 1000)
        query = self._sign(params)
        url = f'{base_url}{path}?{query}'
        req = urllib.request.Request(url, headers={'X-MBX-APIKEY': self.api_key, **self.headers})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {'code': '-1', 'msg': str(e)}

    def _private_post(self, base_url: str, path: str, params: dict = None) -> dict:
        if not self.api_key:
            return {'code': '-1', 'msg': 'API key not configured'}
        params = params or {}
        params['timestamp'] = int(time.time() * 1000)
        query = self._sign(params)
        url = f'{base_url}{path}?{query}'
        body = params
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={'X-MBX-APIKEY': self.api_key,
                                              'Content-Type': 'application/json',
                                              **self.headers})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {'code': '-1', 'msg': str(e)}

    def _convert_symbol(self, symbol: str) -> str:
        """将通用格式 BTC-USDT-SWAP 转为 Binance 格式 BTCUSDT"""
        return symbol.replace('-', '').replace('SWAP', '').strip()

    def fetch_ohlcv(self, symbol: str, timeframe: str = '4H',
                    limit: int = 100) -> pd.DataFrame:
        tf_map = {'1H': '1h', '4H': '4h', '1d': '1d'}
        s = self._convert_symbol(symbol)
        result = self._public_get(self.base_url,
            f'/api/v3/klines?symbol={s}&interval={tf_map.get(timeframe, "4h")}&limit={limit}')
        if isinstance(result, list):
            candles = []
            for c in result:
                candles.append({
                    'timestamp': pd.to_datetime(c[0], unit='ms', utc=True),
                    'open': float(c[1]), 'high': float(c[2]),
                    'low': float(c[3]), 'close': float(c[4]),
                    'volume': float(c[5]),
                })
            df = pd.DataFrame(candles).set_index('timestamp')
            self._add_technical_features(df)
            return df
        return pd.DataFrame()

    def _add_technical_features(self, df: pd.DataFrame):
        df['returns'] = df['close'].pct_change()
        tr = pd.concat([df['high']-df['low'],
                        (df['high']-df['close'].shift(1)).abs(),
                        (df['low']-df['close'].shift(1)).abs()], axis=1).max(axis=1)
        df['atr_14'] = tr.rolling(14).mean()
        df['high_20d'] = df['high'].rolling(20).max()
        df['dd_from_20d_high'] = (df['close'] - df['high_20d']) / df['high_20d']
        df['ret_24h'] = df['close'].pct_change(1)
        return df

    def fetch_ticker(self, symbol: str) -> dict:
        s = self._convert_symbol(symbol)
        result = self._public_get(self.base_url, f'/api/v3/ticker/24hr?symbol={s}')
        if isinstance(result, dict) and 'lastPrice' in result:
            return {'symbol': symbol, 'price': float(result.get('lastPrice', 0)),
                    'bid': float(result.get('bidPrice', 0)), 'ask': float(result.get('askPrice', 0)),
                    'volume_24h': float(result.get('volume', 0)),
                    'high_24h': float(result.get('highPrice', 0)),
                    'low_24h': float(result.get('lowPrice', 0)),
                    'change_24h': float(result.get('priceChangePercent', 0))}
        return {'symbol': symbol, 'price': 0}

    def fetch_funding_rate(self, symbol: str) -> float:
        s = self._convert_symbol(symbol) + 'USDT'
        result = self._public_get(self.fapi_url, f'/fapi/v1/fundingRate?symbol={s}&limit=1')
        if isinstance(result, list) and result:
            return float(result[-1].get('fundingRate', 0))
        return 0.0

    def fetch_open_interest(self, symbol: str) -> float:
        s = self._convert_symbol(symbol)
        result = self._public_get(self.fapi_url, f'/futures/data/openInterestHist?symbol={s}USDT&period=5m&limit=1')
        if isinstance(result, list) and result:
            return float(result[0].get('sumOpenInterest', 0))
        return 0.0

    def place_order(self, symbol: str, side: str, size: float,
                    order_type: str = 'market', price: float = None,
                    lever: int = 1, reduce_only: bool = False) -> dict:
        s = self._convert_symbol(symbol)
        params = {'symbol': f'{s}USDT', 'side': side.upper(),
                  'type': order_type.upper(), 'quantity': size}
        if price and order_type == 'limit':
            params['price'] = price
        if reduce_only:
            params['reduceOnly'] = 'true'
        result = self._private_post(self.fapi_url, '/fapi/v1/order', params)
        if 'orderId' in result:
            return {'success': True, 'order_id': str(result['orderId']),
                    'fill_price': result.get('avgPrice', '0')}
        return {'success': False, 'error': result.get('msg', 'Unknown'), 'code': result.get('code')}

    def cancel_order(self, symbol: str, order_id: str) -> dict:
        s = self._convert_symbol(symbol)
        params = {'symbol': f'{s}USDT', 'orderId': order_id}
        result = self._private_delete(self.fapi_url, '/fapi/v1/order', params)
        return {'success': result.get('code') == 200 if isinstance(result, dict) else True}

    def get_positions(self, symbol: str = None) -> List[dict]:
        result = self._private_get(self.fapi_url, '/fapi/v2/positionRisk')
        positions = []
        if isinstance(result, list):
            for p in result:
                pos_amt = float(p.get('positionAmt', 0))
                if pos_amt == 0:
                    continue
                positions.append({
                    'exchange': 'Binance', 'symbol': p.get('symbol'),
                    'position': pos_amt,
                    'avg_price': float(p.get('entryPrice', 0)),
                    'mark_price': float(p.get('markPrice', 0)),
                    'unrealized_pnl': float(p.get('unRealizedProfit', 0)),
                    'leverage': int(float(p.get('leverage', 1))),
                    'liquidation_price': float(p.get('liquidationPrice', 0)) if p.get('liquidationPrice') else None,
                    'margin': abs(pos_amt * float(p.get('markPrice', 0))) / int(float(p.get('leverage', 1))),
                })
        return positions

    def get_balance(self, ccy: str = 'USDT') -> float:
        result = self._private_get(self.fapi_url, '/fapi/v2/balance')
        if isinstance(result, list):
            for a in result:
                if a.get('asset') == ccy:
                    return float(a.get('availableBalance', 0))
        return 0.0

    def get_account_summary(self) -> dict:
        summary = {'exchange': 'Binance', 'total_equity': 0, 'available': 0,
                   'margin_used': 0, 'positions': [], 'timestamp': str(datetime.now())}
        # Balance
        bal = self._private_get(self.fapi_url, '/fapi/v2/account')
        if isinstance(bal, dict):
            summary['total_equity'] = float(bal.get('totalWalletBalance', 0))
            summary['available'] = float(bal.get('availableBalance', 0))
        summary['positions'] = self.get_positions()
        summary['margin_used'] = sum(p.get('margin', 0) for p in summary['positions'])
        summary['margin_ratio'] = (summary['margin_used'] / summary['total_equity']
                                    if summary['total_equity'] > 0 else 0)
        return summary

    def download_historical_data(self, symbol: str, start_date: str,
                                 end_date: str) -> pd.DataFrame:
        import ccxt
        ex = ccxt.binance({'enableRateLimit': True})
        since = ex.parse8601(start_date.replace('-', '') + 'T00:00:00Z')
        s = self._convert_symbol(symbol) + '/USDT'
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
