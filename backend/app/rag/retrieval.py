from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.ai.embeddings import get_embedding_provider


def get_lexical_search(db: Session, query: str, user_id: int, limit: int = 20) -> List[DocumentChunk]:
    """
    Performs keyword matching query. On PostgreSQL, utilizes full-text search vectors. 
    On SQLite, falls back to wildcard keyword contains clauses. (Tenant Isolated).
    """
    dialect = db.bind.dialect.name
    q = (
        db.query(DocumentChunk)
        .join(Document, Document.id == DocumentChunk.document_id)
        .filter(DocumentChunk.user_id == user_id)
    )
    
    # Extract search terms to filter noise
    terms = [t for t in query.split() if len(t) > 2]
    if not terms:
        terms = [query]
        
    if dialect == "postgresql":
        from sqlalchemy import func
        # PostgreSQL native full-text search matching
        q = q.filter(
            func.to_tsvector("english", DocumentChunk.text).op("@@")(
                func.plainto_tsquery("english", query)
            )
        )
    else:
        # SQLite test environment fallback: standard ILIKE wildcard searches
        conditions = [DocumentChunk.text.ilike(f"%{term}%") for term in terms]
        q = q.filter(or_(*conditions))
        
    return q.limit(limit).all()


def get_semantic_search(
    db: Session, query_vector: List[float], user_id: int, limit: int = 20
) -> List[Tuple[DocumentChunk, float]]:
    """
    Performs vector similarity search on pgvector (PostgreSQL). 
    On SQLite, retrieves chunks and computes cosine similarity in python space.
    """
    dialect = db.bind.dialect.name
    
    if dialect == "postgresql":
        # cosine_distance in pgvector ranges from 0 to 2. Similarity = 1 - distance.
        distance_expr = DocumentChunk.embedding.cosine_distance(query_vector)
        results = (
            db.query(DocumentChunk, (1.0 - distance_expr).label("similarity"))
            .join(Document, Document.id == DocumentChunk.document_id)
            .filter(DocumentChunk.user_id == user_id)
            .order_by(distance_expr)
            .limit(limit)
            .all()
        )
        return [(row[0], float(row[1])) for row in results]
    else:
        # SQLite test environment fallback: compute cosine similarity in python
        chunks = (
            db.query(DocumentChunk)
            .join(Document, Document.id == DocumentChunk.document_id)
            .filter(DocumentChunk.user_id == user_id)
            .all()
        )
        scores: List[Tuple[DocumentChunk, float]] = []
        
        for c in chunks:
            if not c.embedding:
                continue
            
            # Math: A . B / (||A|| * ||B||)
            dot = sum(x * y for x, y in zip(query_vector, c.embedding))
            norm_q = sum(x * x for x in query_vector) ** 0.5
            norm_c = sum(x * x for x in c.embedding) ** 0.5
            similarity = dot / (norm_q * norm_c) if norm_q and norm_c else 0.0
            scores.append((c, similarity))
            
        scores.sort(key=lambda item: item[1], reverse=True)
        return scores[:limit]


def hybrid_retrieval(
    db: Session, query: str, user_id: int, limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Combines semantic and lexical retrieval engines.
    Merges and ranks results using Reciprocal Rank Fusion (RRF) for high recall.
    """
    # 1. Fetch query vector
    provider = get_embedding_provider()
    query_vector = provider.get_embedding(query)
    
    # 2. Fetch retrieval candidate lists
    lexical_candidates = get_lexical_search(db, query, user_id, limit=20)
    semantic_candidates_with_sim = get_semantic_search(db, query_vector, user_id, limit=20)
    
    semantic_candidates = [item[0] for item in semantic_candidates_with_sim]
    semantic_sim_map = {item[0].id: item[1] for item in semantic_candidates_with_sim}
    
    # 3. Calculate Reciprocal Rank Fusion (RRF)
    # RRF Score = 1/(60 + r_lexical) + 1/(60 + r_semantic)
    rrf_scores: Dict[int, float] = {}
    
    for rank, chunk in enumerate(lexical_candidates):
        rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (60.0 + rank + 1))
        
    for rank, chunk in enumerate(semantic_candidates):
        rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (60.0 + rank + 1))
        
    # Gather chunks dictionary
    all_chunks = {c.id: c for c in lexical_candidates + semantic_candidates}
    
    # Sort IDs by RRF value descending
    sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
    
    # 4. Construct response list with parent document filename citations
    results = []
    for cid in sorted_ids[:limit]:
        chunk = all_chunks[cid]
        doc = db.query(Document).filter(Document.id == chunk.document_id).first()
        filename = doc.filename if doc else "Unknown Source"
        
        results.append({
            "chunk": chunk,
            "rrf_score": rrf_scores[cid],
            "similarity": semantic_sim_map.get(cid, 0.0),
            "filename": filename
        })
        
    return results
