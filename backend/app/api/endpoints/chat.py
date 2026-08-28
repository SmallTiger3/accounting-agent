from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from ...db.session import get_db
from ...models.chat import ChatSession, ChatMessage
from ...models.user import User
from ...schemas.chat import ChatMessageCreate, ChatResponse
from ...api.deps import get_current_user
from ...agent.accounting_agent import AccountingAgent

router = APIRouter(prefix="/chat", tags=["AI对话"])

agent = AccountingAgent()


@router.get("/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取对话历史列表"""
    result = await db.execute(
        select(ChatSession).where(ChatSession.user_id == current_user.id).order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    
    session_list = []
    for session in sessions:
        count_result = await db.execute(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session.id)
        )
        msg_count = count_result.scalar_one()
        
        last_msg_result = await db.execute(
            select(ChatMessage.content).where(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at.desc()).limit(1)
        )
        last_msg = last_msg_result.scalar_one_or_none()
        
        session_list.append({
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "message_count": msg_count,
            "last_message": last_msg[:100] if last_msg else None,
        })
    
    return session_list


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取对话历史消息"""
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "tool_name": msg.tool_name,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in messages
    ]


@router.post("/message", response_model=ChatResponse)
async def send_message(
    message_data: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发送消息给AI"""
    session = None
    if message_data.session_id:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == message_data.session_id,
                ChatSession.user_id == current_user.id,
            )
        )
        session = result.scalar_one_or_none()
    
    if not session:
        session = ChatSession(user_id=current_user.id, title=message_data.content[:50])
        db.add(session)
        await db.flush()
    
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=message_data.content,
    )
    db.add(user_msg)
    await db.flush()
    
    history_result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at).limit(20)
    )
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in history_result.scalars().all()
    ]
    
    try:
        response = await agent.chat(
            db=db,
            user_id=current_user.id,
            message=message_data.content,
            chat_history=history[:-1],
        )
    except Exception:
        # LLM 或工具调用异常（如模型超时/限流），回滚本次事务并返回友好提示
        await db.rollback()
        raise HTTPException(status_code=502, detail="AI 服务暂时不可用，请稍后重试")
    
    ai_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=response["content"],
    )
    db.add(ai_msg)
    try:
        await db.flush()
    except SQLAlchemyError:
        # 工具调用中的 SQL 错误可能已中止事务，回滚并返回友好提示
        await db.rollback()
        raise HTTPException(status_code=502, detail="AI 处理失败，请稍后重试")
    
    if not session.title or session.title == message_data.content[:50]:
        session.title = message_data.content[:50]
    
    await db.flush()
    
    return {
        "session_id": session.id,
        "message": {
            "id": ai_msg.id,
            "role": "assistant",
            "content": ai_msg.content,
            "tool_name": None,
            "created_at": ai_msg.created_at,
        },
        "budget_alerts": response.get("budget_alerts"),
    }


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除对话会话"""
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await db.delete(session)
    await db.flush()
