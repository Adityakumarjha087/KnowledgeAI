from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.document import Document
from app.models.feedback import Feedback
from app.models.observability import QueryLog
from app.evaluation.eval import evaluate_rag_pipeline

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def get_system_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Computes system-wide performance and cost metrics for the dashboard.
    In a multi-tenant layout, non-admins can view global aggregates without identifying records.
    """
    total_users = db.query(User).count()
    total_documents = db.query(Document).count()
    total_questions = db.query(QueryLog).count()
    
    # Aggregate Latencies
    avg_total = db.query(func.avg(QueryLog.total_latency)).scalar() or 0.0
    avg_retrieval = db.query(func.avg(QueryLog.retrieval_latency)).scalar() or 0.0
    
    # Aggregate Costs & Usage
    total_tokens = db.query(func.sum(QueryLog.tokens_used)).scalar() or 0
    total_cost = db.query(func.sum(QueryLog.estimated_cost)).scalar() or 0.0
    
    # Helpfulness Feedback Rates
    total_feedback = db.query(Feedback).count()
    positive_feedback = db.query(Feedback).filter(Feedback.rating == 1).count()
    helpfulness_pct = (
        (positive_feedback / total_feedback) * 100.0 if total_feedback else 0.0
    )
    
    # Errors tracking
    total_errors = db.query(QueryLog).filter(QueryLog.errors.isnot(None)).count()
    error_pct = (total_errors / total_questions) * 100.0 if total_questions else 0.0
    
    return {
        "total_users": total_users,
        "total_documents": total_documents,
        "total_questions": total_questions,
        "average_response_time_sec": round(avg_total, 2),
        "average_retrieval_time_sec": round(avg_retrieval, 2),
        "total_tokens_used": int(total_tokens),
        "total_estimated_cost_usd": round(total_cost, 4),
        "total_feedback_submissions": total_feedback,
        "helpfulness_rating_percent": round(helpfulness_pct, 1),
        "error_rate_percent": round(error_pct, 1)
    }


@router.get("/evaluation")
def run_evaluation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Benchmarks RAG faithfulness, answer relevance, context recall, 
    and citation accuracy against the standard golden validation dataset.
    """
    return evaluate_rag_pipeline(db, current_user.id)
