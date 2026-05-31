# -*- mode: python ; coding: utf-8 -*-
"""
AIQuant Engine - PyInstaller spec
打包成独立的 macOS .app
"""
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['gui/tui.py'],
    pathex=[str(Path(__file__).parent)],
    binaries=[],
    datas=[
        ('exchange', 'exchange'),
        ('notify', 'notify'),
        ('review', 'review'),
        ('evolution', 'evolution'),
        ('goal', 'goal'),
        ('mcp', 'mcp'),
        ('config.toml.example', '.'),
        ('README.md', '.'),
        ('README_CN.md', '.'),
    ],
    hiddenimports=[
        'signals', 'risk_manager', 'market_regime', 'ai_router',
        'order_executor', 'config_loader', 'results_analyzer',
        'real_portfolio', 'backtester', 'data_loader',
        'exchange.okx', 'exchange.binance', 'exchange.gate',
        'exchange.factory', 'exchange.base',
        'notify.channels.telegram', 'notify.channels.wechat',
        'notify.channels.discord', 'notify.channels.qq', 'notify.channels.email',
        'review.analyzer',
        'evolution.manager',
        'goal.planner',
        'mcp.prompt_bar',
        'textual', 'rich',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'scipy', 'cv2', 'PIL',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AIQuantEngine',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='AIQuant Engine.app',
    icon=None,
    bundle_identifier='com.aiquant.engine',
    info_plist={
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleVersion': '2.0.0',
        'CFBundleDisplayName': 'AIQuant Engine',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15',
    },
)
