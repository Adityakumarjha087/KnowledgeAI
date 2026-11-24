from app.ingestion.splitter import clean_text, split_text


def test_clean_text_strips_null_bytes_and_collapses_spaces_but_keeps_newlines():
    assert clean_text("  a\x00b \t  c\n\nd  ") == "ab c\n\nd"


def test_page_markers_are_removed_and_assign_page_numbers():
    text = "[PAGE_1]\nFirst page body.\n\n[PAGE_3]\nThird page body."
    chunks = split_text(text, chunk_size=500, chunk_overlap=50)

    assert [c["page_number"] for c in chunks] == [1, 3]
    assert all("[PAGE_" not in c["text"] for c in chunks)
    assert chunks[1]["text"] == "Third page body."


def test_markdown_headings_set_section_and_start_a_new_chunk():
    text = "# Refund Policy\n\nRefunds take five days.\n\n# Shipping\n\nShipping takes two days."
    chunks = split_text(text, chunk_size=500, chunk_overlap=50)

    sections = [c["section"] for c in chunks]
    assert "Refund Policy" in sections
    assert "Shipping" in sections
    shipping = [c for c in chunks if c["section"] == "Shipping"]
    assert all("Refunds take five days." not in c["text"] for c in shipping)


def test_oversized_paragraph_is_split_on_sentences_within_limit():
    sentences = [f"Sentence number {i} is here." for i in range(10)]
    chunks = split_text(" ".join(sentences), chunk_size=80, chunk_overlap=10)

    assert len(chunks) > 1
    assert all(len(c["text"]) <= 80 + 1 for c in chunks[:-1])
    # No sentence is lost, and the last sentence of a chunk is repeated as overlap.
    joined = " ".join(c["text"] for c in chunks)
    assert all(s in joined for s in sentences)


def test_empty_and_whitespace_only_input_yields_no_chunks():
    assert split_text("", chunk_size=100, chunk_overlap=10) == []
    assert split_text("  \n\n \t ", chunk_size=100, chunk_overlap=10) == []
