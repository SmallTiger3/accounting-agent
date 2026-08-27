from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from ...db.session import get_db
from ...models.chat import ChatSession, ChatMessage
from ...models.user import User
from ...schemas.chat import ChatMessageCreate, ChatResponse, ChatSessionResponse
from ...api.deps import get_current_user
from ...agent.accounting_agent import AccountingAgent

router = APIRouter(prefix="/chat", tags=["AI对话"])

# Agent单例
agent = AccountingAgent()


@router.get("/sessions", response_model=List[ChatSessionResponse])
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
        # 获取消息数量和最后一条消息
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
            "created_at": session.created_at,
            "updated_at": session.updated_at,
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
    # 验证session属于当前用户
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
    # 获取或创建会话
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
    
    # 保存用户消息
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=message_data.content,
    )
    db.add(user_msg)
    await db.flush()
    
    # 获取历史消息用于上下文
    history_result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at).limit(20)
    )
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in history_result.scalars().all()
    ]
    
    # 调用Agent
    response = await agent.chat(
        db=db,
        user_id=current_user.id,
        message=message_data.content,
        chat_history=history[:-1],  # 排除当前消息
    )
    
    # 保存AI回复
    ai_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=response["content"],
    )
    db.add(ai_msg)
    await db.flush()
    
    # 更新会话标题（如果是新会话）
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
