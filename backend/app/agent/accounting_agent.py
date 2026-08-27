import json
from typing import Optional, List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from .llm_factory import create_llm
from .tools import add_transaction, query_transactions, analyze_spending, check_budget, get_spending_insights


SYSTEM_PROMPT = """你是一个专业的记账助手，帮助用户管理个人财务。

你的能力：
1. 自然语言记账 - 用户可以用自然语言描述收支，你会自动解析并记录
2. 智能分类 - 根据描述自动匹配合适的分类
3. 消费分析 - 按时间、分类统计消费情况
4. 预算提醒 - 检查预算使用情况，超支时提醒用户
5. 财务建议 - 基于消费模式提供个性化建议

常见分类参考：
- 支出：餐饮、交通、购物、娱乐、住房、医疗、教育、日用品、通讯、服饰、其他支出
- 收入：工资、奖金、投资收益、兼职、红包、其他收入

回复规则：
- 使用中文回复
- 记账成功后简要确认，并询问是否需要查看分析
- 分析数据时用清晰的格式展示
- 给出实用的财务建议
- 如果用户输入不明确，主动询问确认
"""


class AccountingAgent:
    def __init__(self):
        self.llm = create_llm()
        self.tools = [
            add_transaction,
            query_transactions,
            analyze_spending,
            check_budget,
            get_spending_insights,
        ]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
    
    async def chat(
        self,
        db: AsyncSession,
        user_id: int,
        message: str,
        chat_history: Optional[List[dict]] = None,
    ) -> dict:
        """处理用户消息"""
        
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        
        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=message))
        
        response = await self.llm_with_tools.ainvoke(messages)
        
        tool_results = []
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_args["db"] = db
                tool_args["user_id"] = user_id
                
                for tool in self.tools:
                    if tool.name == tool_name:
                        result = await tool.ainvoke(tool_args)
                        tool_results.append({
                            "tool": tool_name,
                            "result": json.loads(result) if isinstance(result, str) else result,
                        })
                        break
            
            messages.append(response)
            for tr in tool_results:
                tool_msg = f"工具 {tr['tool']} 的结果：{json.dumps(tr['result'], ensure_ascii=False)}"
                messages.append(SystemMessage(content=tool_msg))
            
            response = await self.llm_with_tools.ainvoke(messages)
        
        budget_alerts = []
        for tr in tool_results:
            if tr["tool"] == "check_budget" and tr["result"].get("has_alerts"):
                budget_alerts = tr["result"].get("alerts", [])
        
        return {
            "content": response.content,
            "tool_calls": tool_results,
            "budget_alerts": budget_alerts,
        }
