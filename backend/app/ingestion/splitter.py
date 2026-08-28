import re
from typing import List, Dict, Any, Optional
from app.core.config import settings


def clean_text(text: str) -> str:
    """Removes null bytes and normalizes horizontal spaces, preserving newlines"""
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_text(
    text: str, 
    chunk_size: Optional[int] = None, 
    chunk_overlap: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Intelligently splits a document string into metadata-aware text chunks.
    Reads PDF page markers [PAGE_x], tracks sections (# Title), merges paragraphs,
    implements chunk character overlaps, and returns lists of structured metadata.
    """
    if chunk_size is None:
        chunk_size = settings.CHUNK_SIZE
    if chunk_overlap is None:
        chunk_overlap = settings.CHUNK_OVERLAP

    cleaned_text = clean_text(text)
    paragraphs = cleaned_text.split("\n\n")
    
    chunks: List[Dict[str, Any]] = []
    current_chunk_paras: List[str] = []
    current_length = 0
    current_page = 1
    current_section = None
    
    page_pattern = re.compile(r"\[PAGE_(\d+)\]")
    section_pattern = re.compile(r"^(#+\s+.+|[A-Z\s]{4,30})$")

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # Detect page number indicators
        page_matches = page_pattern.findall(para)
        if page_matches:
            # Commit pending chunks before changing page context
            if current_chunk_paras:
                chunks.append({
                    "text": "\n\n".join(current_chunk_paras),
                    "page_number": current_page,
                    "section": current_section
                })
                current_chunk_paras = []
                current_length = 0
            current_page = int(page_matches[-1])
            # Strip page tags so they do not pollute search results
            para = page_pattern.sub("", para).strip()
            
        # Detect section headings (Markdown or capitalized titles)
        if section_pattern.match(para):
            # Commit pending chunks before changing section context
            if current_chunk_paras:
                chunks.append({
                    "text": "\n\n".join(current_chunk_paras),
                    "page_number": current_page,
                    "section": current_section
                })
                current_chunk_paras = []
                current_length = 0
            current_section = para.lstrip("#").strip()
            
        para_len = len(para)
        
        # If a single paragraph exceeds the chunk size limit, split it by sentence
        if para_len > chunk_size:
            if current_chunk_paras:
                chunks.append({
                    "text": "\n\n".join(current_chunk_paras),
                    "page_number": current_page,
                    "section": current_section
                })
                current_chunk_paras = []
                current_length = 0

                
            sentences = re.split(r"(?<=[.!?])\s+", para)
            sub_chunk_sents: List[str] = []
            sub_len = 0
            for sent in sentences:
                sent_len = len(sent)
                if sub_len + sent_len > chunk_size:
                    if sub_chunk_sents:
                        chunks.append({
                            "text": " ".join(sub_chunk_sents),
                            "page_number": current_page,
                            "section": current_section
                        })
                        # Backtrack sentence overlap (keep the last sentence for overlap)
                        sub_chunk_sents = [sub_chunk_sents[-1]] if sub_chunk_sents else []
                        sub_len = sum(len(s) for s in sub_chunk_sents)
                sub_chunk_sents.append(sent)
                sub_len += sent_len
                
            if sub_chunk_sents:
                current_chunk_paras = [" ".join(sub_chunk_sents)]
                current_length = len(current_chunk_paras[0])
            continue
            
        # Paragraph merges to form chunk
        if current_length + para_len > chunk_size:
            if current_chunk_paras:
                chunks.append({
                    "text": "\n\n".join(current_chunk_paras),
                    "page_number": current_page,
                    "section": current_section
                })
                
            # Carry over paragraphs for chunk overlap
            overlap_paras = []
            overlap_len = 0
            for p in reversed(current_chunk_paras):
                if overlap_len + len(p) < chunk_overlap:
                    overlap_paras.insert(0, p)
                    overlap_len += len(p)
                else:
                    break
            
            current_chunk_paras = overlap_paras
            current_chunk_paras.append(para)
            current_length = sum(len(x) for x in current_chunk_paras) + len(current_chunk_paras) - 1
        else:
            current_chunk_paras.append(para)
            current_length += para_len + (2 if current_length > 0 else 0)

    # Append remaining slice
    if current_chunk_paras:
        chunks.append({
            "text": "\n\n".join(current_chunk_paras),
            "page_number": current_page,
            "section": current_section
        })
        
    return chunks
