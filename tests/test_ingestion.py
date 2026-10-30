"""Parser + seeding tests. Real-PDF tests are skipped unless the textbook is available
(set ANATOMIND_TEST_PDF or place it at backend/data/)."""
import os
import runpy
import sys
from pathlib import Path

import pytest

from app.services.textbook_parser import Paragraph, chunk_paragraphs

PDF = os.environ.get("ANATOMIND_TEST_PDF") or str(Path(__file__).resolve().parent.parent / "backend" / "data"
                                                   / "anatomy-and-physiology-2e_-_WEB.pdf")
needs_pdf = pytest.mark.skipif(not Path(PDF).exists(), reason="textbook PDF not available")


def test_chunking_respects_size_and_keeps_pages():
    paras = [Paragraph("Sentence one is here. " * 40, 5), Paragraph("Short paragraph.", 6)]
    chunks = chunk_paragraphs(paras, max_chars=300)
    assert all(len(c.content) <= 300 for c in chunks) and len(chunks) > 2
    assert chunks[-1].page_end == 6 and [c.index for c in chunks] == list(range(len(chunks)))


def test_chunking_splits_unpunctuated_text():
    chunks = chunk_paragraphs([Paragraph("x" * 1000, 1)], max_chars=400)
    assert len(chunks) == 3 and all(len(c.content) <= 400 for c in chunks)


@needs_pdf
def test_parse_real_pdf_chapter_1():
    from app.services.textbook_parser import parse_pdf
    ch = parse_pdf(PDF, {1})[0]
    assert ch.title == "An Introduction to the Human Body" and ch.unit_title == "Levels of Organization"
    assert [s.number for s in ch.sections] == [f"1.{i}" for i in range(1, 8)]      # 1.1 .. 1.7 only (no Key Terms etc.)
    homeo = next(s for s in ch.sections if s.title == "Homeostasis")
    assert [c.title for c in homeo.concepts] == ["Overview", "Negative Feedback", "Positive Feedback"]
    text = " ".join(p.text for c in homeo.concepts for p in c.paragraphs)
    assert "set point" in text and "Access for free" not in text and "http" not in text


@needs_pdf
def test_seed_script_ingests_idempotently(monkeypatch):
    from conftest import FakeEmbedder
    from app.database import Base, SessionLocal, engine
    from app.models import Concept, TextbookChunk
    from app.services import embeddings
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    embeddings.set_embedder(FakeEmbedder())
    script = str(Path(__file__).resolve().parent.parent / "backend" / "scripts" / "seed_from_pdf.py")
    monkeypatch.setattr(sys, "argv", ["seed", "--pdf", PDF, "--chapters", "1"])
    ns = runpy.run_path(script, run_name="seed_test")
    assert ns["main"]() == 0
    with SessionLocal() as db:
        n_c, n_k = db.query(Concept).count(), db.query(TextbookChunk).count()
        chunk = db.query(TextbookChunk).filter(TextbookChunk.concept_id.like("ch1-s5-%")).first()
    assert n_c > 10 and n_k >= n_c and len(chunk.embedding) == 384 * 4
    assert chunk.source_metadata["source"] == "OpenStax Anatomy and Physiology 2e" and chunk.source_metadata["pdf_pages"]
    assert ns["main"]() == 0                                   # second run: nothing duplicated
    with SessionLocal() as db:
        assert (db.query(Concept).count(), db.query(TextbookChunk).count()) == (n_c, n_k)
