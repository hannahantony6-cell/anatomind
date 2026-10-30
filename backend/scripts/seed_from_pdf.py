#!/usr/bin/env python
"""Ingest the OpenStax Anatomy & Physiology 2e PDF into SQLite (concepts + embedded chunks).

Usage (from the backend/ folder):
    python scripts/seed_from_pdf.py                      # full ingestion (needs the embedding model)
    python scripts/seed_from_pdf.py --dry-run            # parse only, print statistics, write nothing
    python scripts/seed_from_pdf.py --chapters 1,19      # ingest selected chapters only
Safe to re-run: unchanged chunks are skipped, changed ones are updated, nothing is duplicated.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.services.textbook_parser import ParseError, chunk_paragraphs, parse_pdf  # noqa: E402

SOURCE = "OpenStax Anatomy and Physiology 2e"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", default=None, help="Path to the PDF (default: PDF_PATH from .env)")
    ap.add_argument("--chapters", default=None, help="Comma-separated chapter numbers, e.g. 1,19")
    ap.add_argument("--dry-run", action="store_true", help="Parse and report only; no DB, no embeddings")
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--dump-json", default=None, help="Optional path to write the parsed hierarchy as JSON")
    args = ap.parse_args()

    pdf = Path(args.pdf or get_settings().pdf_path)
    if not pdf.exists():
        print(f"ERROR: textbook PDF not found at {pdf}\n"
              "Download 'Anatomy and Physiology 2e' (PDF) from https://openstax.org/details/books/anatomy-and-physiology-2e\n"
              "and place it in backend/data/ (or pass --pdf / set PDF_PATH).", file=sys.stderr)
        return 2
    only = {int(x) for x in args.chapters.split(",")} if args.chapters else None

    t0 = time.time()
    print(f"Parsing {pdf.name} ... (about 30-60 s for the full book)")
    try:
        chapters = parse_pdf(str(pdf), only)
    except ParseError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3
    if not chapters:
        print("ERROR: no chapters matched.", file=sys.stderr)
        return 3

    records = []   # (chapter, section, concept, [TextChunk])
    for ch in chapters:
        for sec in ch.sections:
            for con in sec.concepts:
                records.append((ch, sec, con, chunk_paragraphs(con.paragraphs)))
    n_sections = sum(len(c.sections) for c in chapters)
    n_chunks = sum(len(r[3]) for r in records)
    print(f"Parsed {len(chapters)} chapters, {n_sections} sections, {len(records)} concepts, "
          f"{n_chunks} chunks in {time.time() - t0:.0f}s")

    if args.dump_json:
        Path(args.dump_json).write_text(json.dumps([{
            "chapter": ch.number, "title": ch.title, "unit": ch.unit_title,
            "sections": [{"number": s.number, "title": s.title,
                          "concepts": [{"id": c.id, "title": c.title, "chars": c.text_len} for c in s.concepts]}
                         for s in ch.sections]} for ch in chapters], indent=2))
    if args.dry_run:
        print("Dry run: nothing written.")
        return 0

    from app.database import SessionLocal, init_db
    from app.models import Concept, TextbookChunk
    from app.services.embeddings import get_embedder, to_bytes

    init_db()
    embedder = get_embedder()
    failures: list[str] = []
    new = updated = skipped = 0

    with SessionLocal() as db:
        existing = {c.id: c for c in db.scalars(select(TextbookChunk))}
        concept_rows = {c.id: c for c in db.scalars(select(Concept))}
        pending: list[tuple] = []     # (chunk_id, text_to_embed, row-builder)
        for ch, sec, con, chunks in records:
            ordinal = ch.number * 1_000_000 + int(sec.number.split(".")[1]) * 1000 + con.ordinal  # stable across partial runs
            pages = [p for c in chunks for p in (c.page_start, c.page_end)] or [None]
            fields = dict(
                ordinal=ordinal, unit_id=ch.unit_id, unit_number=ch.unit_number, unit_title=ch.unit_title,
                chapter_id=ch.id, chapter_number=ch.number, chapter_title=ch.title, section_id=sec.id,
                section_number=sec.number, section_title=sec.title, concept_title=con.title,
                page_start=min(pages) if pages[0] else None, page_end=max(pages) if pages[0] else None,
                source_metadata={"source": SOURCE, "license": "CC BY 4.0"})
            row = concept_rows.get(con.id)
            if row:
                for k, v in fields.items():
                    setattr(row, k, v)
            else:
                db.add(Concept(id=con.id, **fields))
            for ck in chunks:
                cid = f"{con.id}#{ck.index}"
                old = existing.get(cid)
                if old and old.content_hash == ck.content_hash:
                    skipped += 1
                    continue
                pending.append((cid, ck, ch, sec, con, old))
        db.flush()

        total = len(pending)
        print(f"{skipped} chunks unchanged, {total} to embed (model: {get_settings().embedding_model})")
        for i in range(0, total, args.batch_size):
            batch = pending[i:i + args.batch_size]
            texts = [f"{b[3].title} | {b[4].title}\n{b[1].content}" for b in batch]  # context-prefixed for embedding
            try:
                vecs = embedder.embed_documents(texts, batch_size=args.batch_size)
            except Exception as e:  # keep going; report at the end
                failures += [f"{b[0]}: {e}" for b in batch]
                continue
            for b, vec in zip(batch, vecs):
                cid, ck, ch, sec, con, old = b
                if vec.shape[0] != get_settings().embedding_dim:
                    failures.append(f"{cid}: unexpected embedding dimension {vec.shape[0]}")
                    continue
                meta = {"source": SOURCE, "pdf_pages": sorted({ck.page_start, ck.page_end}),
                        "section_number": sec.number, "concept_title": con.title, "chunk_index": ck.index}
                if old:
                    old.content, old.content_hash, old.embedding, old.source_metadata = ck.content, ck.content_hash, to_bytes(vec), meta
                    updated += 1
                else:
                    db.add(TextbookChunk(
                        id=cid, unit_id=ch.unit_id, unit_title=ch.unit_title, chapter_id=ch.id,
                        chapter_title=ch.title, section_id=sec.id, section_title=sec.title, concept_id=con.id,
                        chunk_index=ck.index, content=ck.content, content_hash=ck.content_hash,
                        embedding=to_bytes(vec), source_metadata=meta))
                    new += 1
            db.commit()
            print(f"  embedded {min(i + args.batch_size, total)}/{total}", end="\r", flush=True)
        db.commit()

    print(f"\nDone. new={new} updated={updated} unchanged={skipped} failed={len(failures)} "
          f"in {time.time() - t0:.0f}s")
    for f in failures[:20]:
        print("  FAILED:", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
