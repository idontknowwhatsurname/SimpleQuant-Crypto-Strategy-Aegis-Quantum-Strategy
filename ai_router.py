"""
AI Router - 多模型路由模块
支持 DeepSeek / GPT / Claude / Gemini 按任务分配
降低成本：便宜模型做日常分析，贵模型做关键决策
"""
import os
import json
from typing import Optional, Dict, Any
from enum import Enum


class ModelProvider(Enum):
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class TaskType(Enum):
    """任务类型 - 决定使用哪个模型"""
    MARKET_ANALYSIS = "market_analysis"      # 市场分析 → 便宜模型
    SIGNAL_GENERATION = "signal_generation"  # 信号生成 → 便宜模型
    RISK_ASSESSMENT = "risk_assessment"      # 风险评估 → 中等模型
    STRATEGY_REVIEW = "strategy_review"      # 策略复核 → 推理强的模型
    EMERGENCY_DECISION = "emergency_decision"  # 紧急决策 → 快速模型
    NEWS_SENTIMENT = "news_sentiment"        # 新闻情绪 → 便宜模型
    CODE_REVIEW = "code_review"              # 代码审查 → 推理强的模型


# 默认路由配置：按任务类型分配模型
DEFAULT_ROUTING = {
    TaskType.MARKET_ANALYSIS: ModelProvider.DEEPSEEK,
    TaskType.SIGNAL_GENERATION: ModelProvider.DEEPSEEK,
    TaskType.RISK_ASSESSMENT: ModelProvider.OPENAI,
    TaskType.STRATEGY_REVIEW: ModelProvider.ANTHROPIC,
    TaskType.EMERGENCY_DECISION: ModelProvider.OPENAI,
    TaskType.NEWS_SENTIMENT: ModelProvider.DEEPSEEK,
    TaskType.CODE_REVIEW: ModelProvider.ANTHROPIC,
}

# 模型优先级（当首选模型不可用时的备选顺序）
FALLBACK_ORDER = [
    ModelProvider.DEEPSEEK,
    ModelProvider.OPENAI,
    ModelProvider.ANTHROPIC,
    ModelProvider.GOOGLE,
]


class AIRouter:
    """
    多模型路由器
    
    用法:
        router = AIRouter()
        result = router.analyze("分析 BTC 当前市场状态", task_type=TaskType.MARKET_ANALYSIS)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Args:
            config: 配置字典，格式:
                {
                    'api_keys': {
                        'deepseek': 'sk-xxx',
                        'openai': 'sk-xxx',
                        'anthropic': 'sk-xxx',
                        'google': 'xxx'
                    },
                    'routing': {TaskType.MARKET_ANALYSIS: ModelProvider.DEEPSEEK, ...},
                    'fallback_enabled': True
                }
        """
        self.config = config or {}
        self.api_keys = self.config.get('api_keys', self._load_keys_from_env())
        self.routing = self.config.get('routing', DEFAULT_ROUTING)
        self.fallback_enabled = self.config.get('fallback_enabled', True)
        
        # 统计
        self.stats = {provider: {'calls': 0, 'tokens': 0, 'cost': 0.0} 
                      for provider in ModelProvider}
    
    def _load_keys_from_env(self) -> Dict[str, str]:
        """从环境变量加载 API Key"""
        return {
            'deepseek': os.environ.get('DEEPSEEK_API_KEY', ''),
            'openai': os.environ.get('OPENAI_API_KEY', ''),
            'anthropic': os.environ.get('ANTHROPIC_API_KEY', ''),
            'google': os.environ.get('GOOGLE_API_KEY', ''),
        }
    
    def _get_model_for_task(self, task_type: TaskType) -> ModelProvider:
        """根据任务类型获取对应的模型"""
        return self.routing.get(task_type, ModelProvider.DEEPSEEK)
    
    def _call_deepseek(self, prompt: str, **kwargs) -> str:
        """调用 DeepSeek API"""
        try:
            import openai
            client = openai.OpenAI(
                api_key=self.api_keys.get('deepseek', ''),
                base_url='https://api.deepseek.com'
            )
            response = client.chat.completions.create(
                model=kwargs.get('model', 'deepseek-chat'),
                messages=[{'role': 'user', 'content': prompt}],
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 2000)
            )
            self.stats[ModelProvider.DEEPSEEK]['calls'] += 1
            return response.choices[0].message.content
        except Exception as e:
            return f"[DeepSeek Error] {str(e)}"
    
    def _call_openai(self, prompt: str, **kwargs) -> str:
        """调用 OpenAI API"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_keys.get('openai', ''))
            response = client.chat.completions.create(
                model=kwargs.get('model', 'gpt-4o-mini'),
                messages=[{'role': 'user', 'content': prompt}],
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 2000)
            )
            self.stats[ModelProvider.OPENAI]['calls'] += 1
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Error] {str(e)}"
    
    def _call_anthropic(self, prompt: str, **kwargs) -> str:
        """调用 Claude API"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_keys.get('anthropic', ''))
            response = client.messages.create(
                model=kwargs.get('model', 'claude-3-haiku-20240307'),
                max_tokens=kwargs.get('max_tokens', 2000),
                messages=[{'role': 'user', 'content': prompt}]
            )
            self.stats[ModelProvider.ANTHROPIC]['calls'] += 1
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Error] {str(e)}"
    
    def _call_google(self, prompt: str, **kwargs) -> str:
        """调用 Gemini API"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_keys.get('google', ''))
            model = genai.GenerativeModel(kwargs.get('model', 'gemini-pro'))
            response = model.generate_content(prompt)
            self.stats[ModelProvider.GOOGLE]['calls'] += 1
            return response.text
        except Exception as e:
            return f"[Google Error] {str(e)}"
    
    def _call_model(self, provider: ModelProvider, prompt: str, **kwargs) -> str:
        """调用指定模型"""
        if provider == ModelProvider.DEEPSEEK:
            return self._call_deepseek(prompt, **kwargs)
        elif provider == ModelProvider.OPENAI:
            return self._call_openai(prompt, **kwargs)
        elif provider == ModelProvider.ANTHROPIC:
            return self._call_anthropic(prompt, **kwargs)
        elif provider == ModelProvider.GOOGLE:
            return self._call_google(prompt, **kwargs)
        else:
            return f"[Error] Unknown provider: {provider}"
    
    def analyze(self, prompt: str, task_type: TaskType = TaskType.MARKET_ANALYSIS, 
                **kwargs) -> str:
        """
        智能分析入口 - 自动选择最佳模型
        
        Args:
            prompt: 分析提示词
            task_type: 任务类型
            **kwargs: 传递给模型的额外参数
        
        Returns:
            模型返回的文本
        """
        primary_provider = self._get_model_for_task(task_type)
        
        # 尝试主模型
        result = self._call_model(primary_provider, prompt, **kwargs)
        
        # 如果失败且启用 fallback，尝试其他模型
        if result.startswith('[') and 'Error' in result and self.fallback_enabled:
            for fallback_provider in FALLBACK_ORDER:
                if fallback_provider == primary_provider:
                    continue
                # 检查是否有 API Key
                if self.api_keys.get(fallback_provider.value, ''):
                    result = self._call_model(fallback_provider, prompt, **kwargs)
                    if not result.startswith('['):
                        break
        
        return result
    
    def analyze_market(self, market_data: dict) -> dict:
        """
        市场分析 - 使用结构化输出
        
        Args:
            market_data: 包含价格、成交量、指标等数据
        
        Returns:
            结构化的分析结果
        """
        prompt = f"""分析以下加密货币市场数据，给出简短的市场状态判断。

数据:
- 币种: {market_data.get('symbol', 'BTC')}
- 当前价格: ${market_data.get('price', 0):,.2f}
- 24h 涨跌: {market_data.get('change_24h', 0):.2%}
- 成交量: ${market_data.get('volume', 0):,.0f}
- RSI(14): {market_data.get('rsi', 50):.1f}
- 资金费率: {market_data.get('funding_rate', 0):.4%}
- 恐惧贪婪指数: {market_data.get('fear_greed', 50)}

请用 JSON 格式返回:
{{
    "regime": "bull/bear/range/volatile",
    "confidence": 0.0-1.0,
    "signal": "long/short/neutral",
    "risk_level": "low/medium/high",
    "reason": "简短原因"
}}"""
        
        result = self.analyze(prompt, task_type=TaskType.MARKET_ANALYSIS)
        
        # 尝试解析 JSON
        try:
            # 提取 JSON 部分
            import re
            json_match = re.search(r'\{[^{}]+\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            'regime': 'unknown',
            'confidence': 0.5,
            'signal': 'neutral',
            'risk_level': 'medium',
            'reason': result[:200]
        }
    
    def get_stats(self) -> dict:
        """获取调用统计"""
        return {
            provider.value: stats 
            for provider, stats in self.stats.items()
        }


# 便捷函数
def quick_analyze(prompt: str, model: str = 'deepseek') -> str:
    """快速分析 - 使用默认配置"""
    router = AIRouter()
    return router.analyze(prompt, task_type=TaskType.MARKET_ANALYSIS)
