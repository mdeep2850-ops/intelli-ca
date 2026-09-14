from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session as DBSession
from langchain_core.messages import HumanMessage, AIMessage
from app.core.database import get_db
from app.schemas.chat import MessageCreate, MessageResponse
from app.models.chat import Session, Message
from app.services.llm import llm_service
from app.core.logger import logger

router = APIRouter()

def get_or_create_session(db: DBSession, session_id: int | None):
    if not session_id:
        new_session = Session(title="Chat Session")
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session
    else:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

def get_session_messages(db: DBSession, session_id: int):
    return db.query(Message).filter(Message.session_id == session_id).order_by(Message.id.asc()).all()

def save_message(db: DBSession, session_id: int, role: str, content: str):
    msg = Message(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()
    return msg

@router.post("/chat", response_model=MessageResponse)
async def chat_endpoint(request: MessageCreate, db: DBSession = Depends(get_db)):
    logger.info(f"Received chat request: {request.content}")
    
    # 1. Get session (synchronous DB call in threadpool)
    session = await run_in_threadpool(get_or_create_session, db, request.session_id)
    session_id = session.id
    
    # 2. Retrieve history
    db_messages = await run_in_threadpool(get_session_messages, db, session_id)

    # 3. Convert to LangChain message types
    langchain_messages = []
    for msg in db_messages:
        if msg.role == "user":
            langchain_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            langchain_messages.append(AIMessage(content=msg.content))

    # 4. Append the new user message
    langchain_messages.append(HumanMessage(content=request.content))

    # 5. Call LLM (async)
    try:
        assistant_response_content = await llm_service.generate_response(langchain_messages)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error calling LLM: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while generating response.")

    # 6. Save the new user message and assistant response to the database
    await run_in_threadpool(save_message, db, session_id, "user", request.content)
    await run_in_threadpool(save_message, db, session_id, "assistant", assistant_response_content)

    logger.info(f"Generated response for session {session_id}")

    return MessageResponse(
        content=assistant_response_content,
        role="assistant",
        session_id=session_id
    )
