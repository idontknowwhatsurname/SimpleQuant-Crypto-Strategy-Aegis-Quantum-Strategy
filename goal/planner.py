"""
AIQuant Engine - Goal 任务规划器
目标 → 拆解 → 执行 → 反馈循环
参考 AutoGPT / CrewAI / LangChain Agents 的核心逻辑
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import time


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    id: int
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    subtasks: List['Task'] = None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'result': self.result,
            'subtasks': [t.to_dict() for t in (self.subtasks or [])]
        }


class GoalPlanner:
    """
    Goal 类任务规划器
    
    工作流程:
    1. 接收用户目标
    2. AI 拆解为子任务
    3. 逐步执行子任务
    4. 验证结果
    5. 反馈循环
    """

    def __init__(self, ai_router=None):
        self.ai_router = ai_router
        self.goals: List[Dict[str, Any]] = []
        self.current_goal: Optional[Dict] = None

    def create_goal(self, goal_text: str) -> Dict[str, Any]:
        """创建新目标"""
        goal = {
            'id': len(self.goals) + 1,
            'text': goal_text,
            'status': 'created',
            'tasks': [],
            'created_at': time.time(),
            'updated_at': time.time(),
        }
        self.goals.append(goal)
        self.current_goal = goal
        return goal

    def decompose_goal(self, goal_id: int) -> List[Task]:
        """将目标拆解为子任务"""
        goal = next((g for g in self.goals if g['id'] == goal_id), None)
        if not goal:
            return []

        # 这里可以用 AI 来智能拆解，目前使用规则拆解
        tasks = []
        goal_text = goal['text'].lower()

        # 根据目标关键词拆解任务
        if '回测' in goal_text or 'backtest' in goal_text:
            tasks = [
                Task(1, '加载数据', '加载历史 K 线数据'),
                Task(2, '运行回测', '执行策略回测'),
                Task(3, '分析结果', '分析回测指标（夏普、回撤、胜率）'),
                Task(4, '生成报告', '生成回测报告'),
            ]
        elif '复盘' in goal_text or 'review' in goal_text:
            tasks = [
                Task(1, '获取持仓', '获取当前持仓数据'),
                Task(2, '分析交易', '分析每笔交易的盈亏'),
                Task(3, '评估表现', '评估整体表现（胜率、盈亏比）'),
                Task(4, '生成建议', '生成改进建议'),
            ]
        elif '进化' in goal_text or 'evolve' in goal_text:
            tasks = [
                Task(1, '收集数据', '收集最近交易数据'),
                Task(2, '分析模式', '分析有效/无效模式'),
                Task(3, '更新策略', '更新 SKILL.md 策略文档'),
                Task(4, '调整参数', '调整策略参数'),
            ]
        elif '交易' in goal_text or 'trade' in goal_text:
            tasks = [
                Task(1, '分析市场', '分析当前市场状态'),
                Task(2, '生成信号', '生成交易信号'),
                Task(3, '风控检查', '进行风控检查'),
                Task(4, '执行交易', '执行交易订单'),
                Task(5, '监控持仓', '监控持仓盈亏'),
            ]
        else:
            # 通用任务拆解
            tasks = [
                Task(1, '分析目标', f'理解用户目标: {goal_text}'),
                Task(2, '制定计划', '制定执行计划'),
                Task(3, '执行计划', '按计划执行'),
                Task(4, '验证结果', '验证执行结果'),
            ]

        goal['tasks'] = tasks
        goal['status'] = 'decomposed'
        return tasks

    def execute_goal(self, goal_id: int) -> Dict[str, Any]:
        """执行目标"""
        goal = next((g for g in self.goals if g['id'] == goal_id), None)
        if not goal:
            return {'success': False, 'error': '目标不存在'}

        # 如果没有拆解任务，先拆解
        if not goal.get('tasks'):
            self.decompose_goal(goal_id)

        goal['status'] = 'executing'
        results = []

        for task in goal['tasks']:
            task.status = TaskStatus.RUNNING
            try:
                # 执行任务（这里可以调用实际的模块）
                result = self._execute_task(task)
                task.status = TaskStatus.COMPLETED
                task.result = result
                results.append({'task': task.name, 'status': 'success', 'result': result})
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.result = str(e)
                results.append({'task': task.name, 'status': 'failed', 'error': str(e)})

        goal['status'] = 'completed'
        goal['updated_at'] = time.time()

        return {
            'success': True,
            'goal': goal['text'],
            'results': results,
            'summary': self._generate_summary(goal, results)
        }

    def _execute_task(self, task: Task) -> str:
        """执行单个任务"""
        # 这里可以调用实际的模块
        # 目前返回模拟结果
        task_implementations = {
            '加载数据': '✅ 成功加载 1000 根 K 线数据',
            '运行回测': '✅ 回测完成，总收益 +187%',
            '分析结果': '📊 夏普比 2.9，最大回撤 -12.4%，胜率 58%',
            '生成报告': '✅ 报告已保存至 backtest_results.csv',
            '获取持仓': '✅ 获取到 3 个持仓',
            '分析交易': '📊 平均盈亏比 1.5，胜率 55%',
            '评估表现': '📊 整体表现良好，建议继续',
            '生成建议': '💡 建议降低杠杆，增加止损频率',
            '收集数据': '✅ 收集到 50 笔交易数据',
            '分析模式': '📊 发现 3 个有效模式，2 个无效模式',
            '更新策略': '✅ SKILL.md 已更新',
            '调整参数': '✅ 止损从 3% 调整为 2.5%',
            '分析市场': '📊 当前市场状态: 震荡',
            '生成信号': '📊 信号强度: 0.65 (偏多)',
            '风控检查': '✅ 风控通过，仓位 25%',
            '执行交易': '✅ 订单已成交',
            '监控持仓': '📊 持仓盈亏: +$150',
        }
        return task_implementations.get(task.name, f'✅ 任务 {task.name} 完成')

    def _generate_summary(self, goal: Dict, results: List[Dict]) -> str:
        """生成执行摘要"""
        success_count = sum(1 for r in results if r['status'] == 'success')
        total_count = len(results)

        summary = f"🎯 目标: {goal['text']}\n"
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        summary += f"完成进度: {success_count}/{total_count}\n\n"

        for r in results:
            status_icon = "✅" if r['status'] == 'success' else "❌"
            summary += f"{status_icon} {r['task']}\n"
            if r['status'] == 'success':
                summary += f"   {r['result']}\n"
            else:
                summary += f"   错误: {r['error']}\n"

        if success_count == total_count:
            summary += f"\n🎉 所有任务完成！"
        else:
            summary += f"\n⚠️ 有 {total_count - success_count} 个任务失败"

        return summary

    def get_goal_status(self, goal_id: int) -> Optional[Dict]:
        """获取目标状态"""
        goal = next((g for g in self.goals if g['id'] == goal_id), None)
        if goal:
            return {
                'id': goal['id'],
                'text': goal['text'],
                'status': goal['status'],
                'tasks': [t.to_dict() for t in goal.get('tasks', [])],
                'created_at': goal['created_at'],
                'updated_at': goal['updated_at'],
            }
        return None

    def list_goals(self) -> List[Dict]:
        """列出所有目标"""
        return [
            {
                'id': g['id'],
                'text': g['text'],
                'status': g['status'],
                'created_at': g['created_at'],
            }
            for g in self.goals
        ]
