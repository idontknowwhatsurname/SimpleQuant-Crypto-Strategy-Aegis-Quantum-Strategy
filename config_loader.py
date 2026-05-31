"""
配置加载器 - 从 TOML 文件和环境变量加载配置
支持 config.toml / 环境变量 / 默认值三级降级
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


CONFIG_PATHS = [
    Path.cwd() / 'config.toml',
    Path.home() / '.okx' / 'config.toml',
]


def load_config(path: Optional[str] = None) -> dict:
    """
    加载配置文件，按优先级：
    1. 显式传入的 path
    2. 当前目录 config.toml
    3. ~/.okx/config.toml
    4. 完全使用环境变量 + 默认值
    """
    config = {}

    # 尝试加载 TOML 文件
    if path:
        paths = [Path(path)]
    else:
        paths = CONFIG_PATHS

    loaded = False
    for p in paths:
        if p.exists():
            try:
                if tomllib:
                    with open(p, 'rb') as f:
                        config = tomllib.load(f)
                else:
                    # 降级：用 dict 解析简单 ini
                    config = _parse_ini_fallback(p)
                print(f"✅ 加载配置文件: {p}")
                loaded = True
                break
            except Exception as e:
                print(f"⚠️ 配置文件解析失败 {p}: {e}")

    if not loaded:
        print("ℹ️  未找到配置文件，使用环境变量 + 默认值")

    # 环境变量覆盖
    _env_override(config)
    return config


def _parse_ini_fallback(path: Path) -> dict:
    """简易 INI 解析器（tomllib 不可用时的降级方案）"""
    config = {}
    current_section = config
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue
            if line.startswith('[') and line.endswith(']'):
                section_name = line[1:-1]
                current_section = {}
                config[section_name] = current_section
            elif '=' in line:
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                # 类型推断
                if val.lower() == 'true':
                    val = True
                elif val.lower() == 'false':
                    val = False
                else:
                    try:
                        val = int(val)
                    except ValueError:
                        try:
                            val = float(val)
                        except ValueError:
                            pass
                current_section[key] = val
    return config


def _env_override(config: dict):
    """环境变量覆盖配置"""
    env_map = {
        'OKX_API_KEY': ('exchange', 'api_key'),
        'OKX_SECRET': ('exchange', 'secret'),
        'OKX_PASSPHRASE': ('exchange', 'passphrase'),
        'DEEPSEEK_API_KEY': ('ai', 'api_keys', 'deepseek'),
        'OPENAI_API_KEY': ('ai', 'api_keys', 'openai'),
        'ANTHROPIC_API_KEY': ('ai', 'api_keys', 'anthropic'),
        'GOOGLE_API_KEY': ('ai', 'api_keys', 'google'),
        'TG_TOKEN': ('notify', 'telegram', 'bot_token'),
        'TG_CHAT': ('notify', 'telegram', 'chat_id'),
    }

    for env_key, config_path in env_map.items():
        value = os.environ.get(env_key)
        if value:
            _set_nested(config, config_path, value)


def _set_nested(d: dict, keys: tuple, value: Any):
    """设置嵌套字典值"""
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


def get_nested(config: dict, keys: tuple, default=None) -> Any:
    """安全获取嵌套字典值"""
    for key in keys:
        if isinstance(config, dict):
            config = config.get(key, {})
        else:
            return default
    return config if config != {} else default


def merge_config(base: dict, override: dict) -> dict:
    """递归合并两个配置字典"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    return result
