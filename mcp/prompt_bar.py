"""
AIQuant Engine - MCP 提示栏
兼容 GPT / DeepSeek / Claude 的多模型提示接口
"""
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ModelProvider(Enum):
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class MCPMessage:
    role: str  # "user" / "assistant" / "system"
    content: str
    model: Optional[str] = None


class MCPPromptBar:
    """
    MCP (Model Context Protocol) 提示栏
    
    功能:
    1. 多模型兼容 (GPT / DeepSeek / Claude)
    2. 任务类型路由
    3. 上下文管理
    4. 响应格式化
    """

    def __init__(self, ai_router=None):
        self.ai_router = ai_router
        self.conversation_history: Dict[str, list] = {}
        self.current_model = ModelProvider.DEEPSEEK

    def set_model(self, model: str):
        """设置当前使用的模型"""
        try:
            self.current_model = ModelProvider(model)
        except ValueError:
            raise ValueError(f"不支持的模型: {model}，支持: {[m.value for m in ModelProvider]}")

    def create_prompt(self, user_input: str, system_prompt: str = None) -> str:
        """创建完整提示"""
        if system_prompt:
            return f"{system_prompt}\n\n用户: {user_input}"
        return user_input

    def route_by_task(self, task_type: str) -> ModelProvider:
        """根据任务类型路由到合适的模型"""
        task_model_map = {
            'market_analysis': ModelProvider.DEEPSEEK,
            'signal_generation': ModelProvider.DEEPSEEK,
            'risk_assessment': ModelProvider.OPENAI,
            'strategy_review': ModelProvider.ANTHROPIC,
            'emergency_decision': ModelProvider.OPENAI,
            'code_review': ModelProvider.ANTHROPIC,
            'quick问答': ModelProvider.DEEPSEEK,
            '深度分析': ModelProvider.ANTHROPIC,
        }
        return task_model_map.get(task_type, self.current_model)

    def format_response(self, response: str, model: ModelProvider) -> str:
        """格式化响应"""
        model_names = {
            ModelProvider.DEEPSEEK: "DeepSeek",
            ModelProvider.OPENAI: "GPT",
            ModelProvider.ANTHROPIC: "Claude",
        }
        return f"[{model_names.get(model, 'AI')}]\n\n{response}"

    def get_conversation(self, session_id: str) -> list:
        """获取会话历史"""
        return self.conversation_history.get(session_id, [])

    def add_to_conversation(self, session_id: str, message: MCPMessage):
        """添加消息到会话历史"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        self.conversation_history[session_id].append(message)

    def clear_conversation(self, session_id: str):
        """清空会话历史"""
        self.conversation_history[session_id] = []

    def analyze_trading_context(self, market_data: Dict[str, Any]) -> str:
        """分析交易上下文"""
        prompt = f"""
当前市场数据:
- 价格: ${market_data.get('price', 0):,.2f}
- 信号: {market_data.get('signal', 0):.4f}
- 市场状态: {market_data.get('regime', 'unknown')}
- 持仓: {json.dumps(market_data.get('positions', []), ensure_ascii=False)}

请分析当前市场状况，给出交易建议。
"""
        return prompt

    def generate_risk_report(self, portfolio_data: Dict[str, Any]) -> str:
        """生成风险报告"""
        prompt = f"""
持仓数据:
{json.dumps(portfolio_data, ensure_ascii=False, indent=2)}

请分析当前持仓风险，包括:
1. 各币种风险敞口
2. 整体杠杆水平
3. 建议的风控措施
"""
        return prompt

    def review_trade(self, trade_data: Dict[str, Any]) -> str:
        """复盘交易"""
        prompt = f"""
交易数据:
{json.dumps(trade_data, ensure_ascii=False, indent=2)}

请复盘这笔交易，包括:
1. 入场时机评估
2. 出场时机评估
3. 盈亏分析
4. 改进建议
"""
        return prompt
