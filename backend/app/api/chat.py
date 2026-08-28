import json
import time
from typing import List, Generator, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, sessionmaker
from app.core.database import get_db

from app.core.config import settings
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.feedback import Feedback
from app.models.observability import QueryLog
from app.schemas.chat import (
    ChatQueryRequest,
    FeedbackCreateRequest,
    FeedbackResponse,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationUpdateTitle
)
from app.rag.retrieval import hybrid_retrieval
from app.rag.reranker import get_reranker
from app.ai.llm import get_llm_provider, calculate_cost
from app.services.memory import rewrite_query

router = APIRouter(tags=["chat"])


def stream_rag_response(
    conversation_id: int,
    user_id: int,
    user_message: str,
    standalone_query: str,
    context_chunks: List[dict],
    session_factory: sessionmaker
) -> Generator[str, None, None]:
    """
    Generator that processes RAG, streams tokens as JSON SSE,
    and commits user/assistant messages + metrics query logs upon stream completion.
    """
    start_time = time.time()
    llm = get_llm_provider()
    
    # 1. Format context and citations
    context_blocks = []
    sources_metadata = []
    for idx, item in enumerate(context_chunks):
        chunk = item["chunk"]
        source_idx = idx + 1
        page_str = f" Page {chunk.page_number}" if chunk.page_number else ""
        sect_str = f" Section '{chunk.section}'" if chunk.section else ""
        
        context_blocks.append(
            f"[{source_idx}] File: {item['filename']}{page_str}{sect_str}\nContent: {chunk.text}"
        )
        sources_metadata.append({
            "source_index": source_idx,
            "document_id": chunk.document_id,
            "filename": item["filename"],
            "page_number": chunk.page_number,
            "section": chunk.section,
            "text": chunk.text[:200] + "..."
        })
        
    context_text = "\n\n".join(context_blocks)
    
    # 2. Yield citation metadata block to client immediately
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources_metadata})}\n\n"
    
    # 3. Assemble Prompts
    system_prompt = (
        "You are a secure, professional Enterprise AI Knowledge Assistant. "
        "Your task is to answer the user's question truthfully, using ONLY the facts provided "
        "in the Context section below. "
        "If the Context does not contain the information required to answer the question, "
        "state clearly and concisely that the information is not available in the uploaded documents. "
        "Do not fabricate or hallucinate any facts.\n\n"
        "Cite the sources you use (e.g. [1], [2]) directly in your sentences when referencing their facts.\n\n"
        f"--- CONTEXT START ---\n{context_text}\n--- CONTEXT END ---"
    )
    
    # Fetch recent history from DB for LLM session
    db_read = session_factory()
    history_msgs = []
    try:
        history_records = (
            db_read.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(10)
            .all()
        )
        history_msgs = [{"role": r.role, "content": r.content} for r in history_records]
    finally:
        db_read.close()

    # 4. Stream LLM Generation and track tokens
    full_response = ""
    retrieval_latency = time.time() - start_time
    llm_start_time = time.time()
    
    try:
        token_stream = llm.generate_stream(system_prompt, user_message, history_msgs)
        for token in token_stream:
            full_response += token
            yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'error': f'Stream generation failed: {str(e)}'})}\n\n"
        return
        
    llm_latency = time.time() - llm_start_time
    total_latency = time.time() - start_time
    
    # Estimate Token Usage
    input_text = system_prompt + user_message + "".join(m["content"] for m in history_msgs)
    input_tokens = len(input_text) // 4
    output_tokens = len(full_response) // 4
    total_tokens = input_tokens + output_tokens
    estimated_cost = calculate_cost(settings.LLM_MODEL, input_tokens, output_tokens)

    # 5. Commit messages and query logs in a fresh DB session
    db_write = session_factory()
    try:
        # Save User Message
        user_msg_record = Message(
            conversation_id=conversation_id,
            role="user",
            content=user_message,
            sources=None
        )
        db_write.add(user_msg_record)
        
        # Save Assistant Message
        assistant_msg_record = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_response,
            sources=sources_metadata
        )
        db_write.add(assistant_msg_record)
        
        # Update Conversation timestamp
        conv = db_write.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            from sqlalchemy.sql import func
            conv.updated_at = func.now()

            
        # Log metrics for observability
        query_log = QueryLog(
            user_id=user_id,
            question=user_message,
            retrieved_chunks=[
                {"chunk_id": item["chunk"].id, "document_id": item["chunk"].document_id, "similarity": item["similarity"]}
                for item in context_chunks
            ],
            retrieval_latency=round(retrieval_latency, 3),
            llm_latency=round(llm_latency, 3),
            total_latency=round(total_latency, 3),
            tokens_used=total_tokens,
            estimated_cost=estimated_cost,
            model_used=settings.LLM_MODEL,
            errors=None
        )
        db_write.add(query_log)
        db_write.commit()
        
        yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_msg_record.id, 'conversation_id': conversation_id})}\n\n"
        
    except Exception as db_err:
        db_write.rollback()
        print(f"Failed to save chat response to database: {str(db_err)}")
        yield f"data: {json.dumps({'type': 'error', 'error': 'Failed to save conversation records.'})}\n\n"
    finally:
        db_write.close()


@router.post("/chat")
def chat_query(
    request: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Initiates RAG query pipeline. Creates a conversation if missing, rewrites
    the query with memory, triggers hybrid retrieval + reranking, and returns an SSE stream.
    """
    conversation_id = request.conversation_id
    
    # 1. Create new conversation if none provided
    if conversation_id is None:
        title = request.message[:40] + ("..." if len(request.message) > 40 else "")
        conv = Conversation(user_id=current_user.id, title=title)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conversation_id = conv.id
    else:
        # Enforce conversation ownership
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conv.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    # 2. Retrieve history for query rewriting
    history_records = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(10)
        .all()
    )
    history_list = [{"role": r.role, "content": r.content} for r in history_records]

    # 3. Rewrite context-dependent queries using memory
    standalone_query = rewrite_query(request.message, history_list)

    # 4. Perform Hybrid search (Semantic + Keywords)
    candidates = hybrid_retrieval(db, standalone_query, current_user.id, limit=15)

    # 5. Apply Context Reranking
    reranker = get_reranker()
    reranked_chunks = reranker.rerank(standalone_query, candidates, top_k=5)

    # Create session factory dynamically bound to the current transaction's engine (handles tests SQLite dynamically!)
    session_factory = sessionmaker(bind=db.bind)

    # 6. Return Server-Sent Events (SSE) Stream
    return StreamingResponse(
        stream_rag_response(
            conversation_id=conversation_id,
            user_id=current_user.id,
            user_message=request.message,
            standalone_query=standalone_query,
            context_chunks=reranked_chunks,
            session_factory=session_factory
        ),
        media_type="text/event-stream"
    )


@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lists chat sessions of the active user ordered by last updated"""
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


@router.get("/conversations/{conv_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieves conversation history details, enforcing user ownership"""
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
    return conv


@router.put("/conversations/{conv_id}", response_model=ConversationResponse)
def update_conversation_title(
    conv_id: int,
    payload: ConversationUpdateTitle,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Updates the title of a conversation, enforcing ownership"""
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this conversation")
    
    conv.title = payload.title
    db.commit()
    db.refresh(conv)
    return conv


@router.delete("/conversations/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deletes conversation session and associated history messages, enforcing ownership"""
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this conversation")
    
    db.delete(conv)
    db.commit()
    return None


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Saves user thumbs rating and comment feedback for a specific AI message"""
    # Verify the message exists and belongs to a conversation owned by the active user
    msg = db.query(Message).filter(Message.id == payload.message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
        
    conv = db.query(Conversation).filter(Conversation.id == msg.conversation_id).first()
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to provide feedback on this message")

    # Insert or update existing feedback
    existing_fb = db.query(Feedback).filter(
        Feedback.message_id == payload.message_id, 
        Feedback.user_id == current_user.id
    ).first()
    
    if existing_fb:
        existing_fb.rating = payload.rating
        existing_fb.feedback = payload.feedback
        db.commit()
        db.refresh(existing_fb)
        return existing_fb
        
    fb = Feedback(
        message_id=payload.message_id,
        user_id=current_user.id,
        rating=payload.rating,
        feedback=payload.feedback
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb
