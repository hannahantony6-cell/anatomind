"""Parse the OpenStax *Anatomy and Physiology 2e* PDF into Unit -> Chapter -> Section -> Concept.

The hierarchy is derived from the PDF itself (nothing is hardcoded):
  * Chapters and section bookmarks come from the PDF outline.
  * Units come from the "UNIT n ..." lines on the printed table-of-contents pages.
  * Concepts are the 10.8pt sub-headings inside a numbered section (e.g. "Negative Feedback").
    Text before the first sub-heading becomes the section's "Overview" concept.

Only numbered sections (e.g. "1.5 Homeostasis") are indexed. Front matter, Key Terms,
Chapter Review, Review/Critical-Thinking Questions, References and the Index are skipped.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

import pymupdf

SECTION_RE = re.compile(r"^(\d+)\.(\d+)\s+(.+)$")
CHAPTER_BM_RE = re.compile(r"^Chapter\s+(\d+)\s+(.+)$")
UNIT_RE = re.compile(r"^UNIT\s+(\d+)\s+(.+)$")
CHAPTER_LINE_RE = re.compile(r"^CHAPTER\s+(\d+)$")
URL_RE = re.compile(r"https?://\S+")

HEADER_Y, FOOTER_Y = 40, 745          # running header / footer bands (PDF points)
MIN_BODY_SIZE = 8.5
SECTION_SIZE, CONCEPT_SIZE = 13.0, 10.8
MIN_CONCEPT_CHARS = 400               # smaller concepts are merged into a neighbour
MAX_CHUNK_CHARS = 1400
SMALL_WORDS = {"and", "of", "the", "in", "to", "for", "a", "an", "on"}


@dataclass
class Paragraph:
    text: str
    page: int


@dataclass
class ParsedConcept:
    id: str
    title: str
    ordinal: int
    paragraphs: list[Paragraph] = field(default_factory=list)

    @property
    def text_len(self) -> int:
        return sum(len(p.text) for p in self.paragraphs)


@dataclass
class ParsedSection:
    id: str
    number: str
    title: str
    concepts: list[ParsedConcept] = field(default_factory=list)


@dataclass
class ParsedChapter:
    id: str
    number: int
    title: str
    unit_id: str
    unit_number: int
    unit_title: str
    start_page: int
    end_page: int
    sections: list[ParsedSection] = field(default_factory=list)


@dataclass
class TextChunk:
    index: int
    content: str
    page_start: int
    page_end: int

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()


class ParseError(RuntimeError):
    pass


def _title_case(s: str) -> str:
    words = s.lower().split()
    return " ".join(w if (i and w in SMALL_WORDS) else w.capitalize() for i, w in enumerate(words))


def parse_units(doc: pymupdf.Document, max_page: int = 20) -> dict[int, tuple[int, str]]:
    """Return {chapter_number: (unit_number, unit_title)} from the printed contents pages."""
    lines: list[str] = []
    for pn in range(0, min(max_page, len(doc))):
        lines += [ln.strip() for ln in doc[pn].get_text().splitlines() if ln.strip()]
    mapping: dict[int, tuple[int, str]] = {}
    cur: tuple[int, str] | None = None
    i = 0
    while i < len(lines):
        m = UNIT_RE.match(lines[i])
        if m:
            title = m.group(2)
            # a unit title can wrap onto the next line ("... AND THE" / "CONTINUITY OF LIFE")
            while i + 1 < len(lines) and not CHAPTER_LINE_RE.match(lines[i + 1]) and lines[i + 1].isupper():
                i += 1
                title += " " + lines[i]
            cur = (int(m.group(1)), _title_case(title))
        else:
            c = CHAPTER_LINE_RE.match(lines[i])
            if c and cur:
                mapping.setdefault(int(c.group(1)), cur)
        i += 1
    return mapping


def _page_lines(page: pymupdf.Page):
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            spans = [s for s in ln["spans"] if s["text"].strip()]
            if not spans:
                continue
            y0 = ln["bbox"][1]
            if y0 < HEADER_Y or y0 > FOOTER_Y:
                continue
            text = "".join(s["text"] for s in ln["spans"]).strip()
            yield spans[0]["size"], spans[0]["font"], text, y0


def _clean(text: str) -> str:
    text = URL_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_pdf(path: str, only_chapters: set[int] | None = None) -> list[ParsedChapter]:
    doc = pymupdf.open(path)
    toc = doc.get_toc()
    if not toc:
        raise ParseError("The PDF has no outline/bookmarks; cannot derive the chapter structure.")
    units = parse_units(doc)
    if not units:
        raise ParseError("Could not read the UNIT headings from the table of contents pages.")

    l1 = [(t[1], t[2]) for t in toc if t[0] == 1]
    chapters: list[ParsedChapter] = []
    for idx, (title, start) in enumerate(l1):
        m = CHAPTER_BM_RE.match(title)
        if not m:
            continue
        num = int(m.group(1))
        if only_chapters and num not in only_chapters:
            continue
        if num not in units:
            raise ParseError(f"Chapter {num} is not listed under any UNIT in the contents pages.")
        end = (l1[idx + 1][1] - 1) if idx + 1 < len(l1) else len(doc)
        u_num, u_title = units[num]
        chapters.append(ParsedChapter(
            id=f"ch{num}", number=num, title=m.group(2).strip(), unit_id=f"unit{u_num}",
            unit_number=u_num, unit_title=u_title, start_page=start, end_page=end))

    for ch in chapters:
        _parse_chapter(doc, ch)
    return chapters


def _parse_chapter(doc: pymupdf.Document, ch: ParsedChapter) -> None:
    section: ParsedSection | None = None
    concept: ParsedConcept | None = None
    buf: list[str] = []
    buf_page = ch.start_page
    last_y = None
    last_page = None
    heading_kind = None  # used to stitch multi-line headings
    heading_page = None
    heading_y = None

    def flush():
        nonlocal buf
        if concept is not None and buf:
            text = _clean(" ".join(buf))
            # drop stray figure-label fragments: very short, no sentence punctuation
            if len(text) >= 25 or text.startswith("•") or re.search(r"[.:?!]$", text):
                concept.paragraphs.append(Paragraph(text, buf_page))
        buf = []

    def new_concept(title: str):
        nonlocal concept
        ordinal = len(section.concepts) + 1
        concept = ParsedConcept(id=f"{section.id}-c{ordinal}", title=title, ordinal=ordinal)
        section.concepts.append(concept)

    for pn in range(ch.start_page - 1, ch.end_page):
        for size, font, text, y in _page_lines(doc[pn]):
            is_mulish = "Mulish" in font
            page = pn + 1
            # ---- section heading (13pt) -----------------------------------------------
            if is_mulish and abs(size - SECTION_SIZE) < 0.3:
                if heading_kind == "section" and heading_page == page and y - heading_y < 22 and section:
                    section.title = f"{section.title} {text}".strip()   # wrapped heading
                    heading_y = y
                    continue
                flush()
                m = SECTION_RE.match(text)
                if m and int(m.group(1)) == ch.number:
                    sid = f"{ch.id}-s{int(m.group(2))}"
                    section = ParsedSection(id=sid, number=f"{m.group(1)}.{m.group(2)}", title=m.group(3).strip())
                    ch.sections.append(section)
                    concept = None
                    new_concept("Overview")
                else:
                    section, concept = None, None      # Key Terms / Chapter Review / questions ...
                heading_kind, heading_page, heading_y = "section", page, y
                continue
            if size >= 15:              # chapter title / "Chapter Objectives" end any section
                flush()
                section, concept = None, None
                heading_kind = None
                continue
            if section is None:
                continue
            # ---- concept heading (10.8pt SemiBold) -------------------------------------
            if is_mulish and abs(size - CONCEPT_SIZE) < 0.3 and "SemiBold" in font:
                if heading_kind == "concept" and heading_page == page and y - heading_y < 20 and concept:
                    concept.title = f"{concept.title} {text}".strip()
                    heading_y = y
                    continue
                flush()
                if concept is not None and concept.title == "Overview" and not concept.paragraphs:
                    section.concepts.pop()          # nothing before the first sub-heading
                new_concept(text.strip())
                heading_kind, heading_page, heading_y = "concept", page, y
                continue
            # ---- body text ---------------------------------------------------------------
            heading_kind = None
            if size < MIN_BODY_SIZE or "Access for free" in text or concept is None:
                continue
            new_para = last_page != page or last_y is None or (y - last_y) > 17
            if new_para:
                flush()
                buf_page = page
            buf.append(text)
            last_y, last_page = y, page
    flush()
    for sec in ch.sections:
        _merge_small(sec)


def _merge_small(sec: ParsedSection) -> None:
    """Merge concepts shorter than MIN_CONCEPT_CHARS into the previous (or next) concept."""
    merged: list[ParsedConcept] = []
    carry: ParsedConcept | None = None
    for c in sec.concepts:
        if not c.paragraphs:
            continue
        if carry is not None:                       # a small leading concept waiting for a home
            head = [Paragraph(carry.title, carry.paragraphs[0].page)] if carry.title != "Overview" else []
            c.paragraphs = head + carry.paragraphs + c.paragraphs
            carry = None
        if c.text_len < MIN_CONCEPT_CHARS:
            if merged:
                prev = merged[-1]
                if c.title != "Overview":
                    prev.paragraphs.append(Paragraph(c.title, c.paragraphs[0].page))
                prev.paragraphs += c.paragraphs
            else:
                carry = c
            continue
        merged.append(c)
    if carry is not None:
        merged.append(carry)
    for i, c in enumerate(merged, 1):
        c.ordinal = i
        c.id = f"{sec.id}-c{i}"
    sec.concepts = merged


def chunk_paragraphs(paragraphs: list[Paragraph], max_chars: int = MAX_CHUNK_CHARS) -> list[TextChunk]:
    """Pack paragraphs into chunks <= max_chars; oversized paragraphs are split on sentences."""
    pieces: list[Paragraph] = []
    for p in paragraphs:
        if len(p.text) <= max_chars:
            pieces.append(p)
            continue
        cur = ""
        for sent in re.split(r"(?<=[.!?])\s+", p.text):
            while len(sent) > max_chars:                       # pathological: no punctuation
                pieces.append(Paragraph(sent[:max_chars], p.page))
                sent = sent[max_chars:]
            if cur and len(cur) + len(sent) + 1 > max_chars:
                pieces.append(Paragraph(cur, p.page))
                cur = sent
            else:
                cur = f"{cur} {sent}".strip()
        if cur:
            pieces.append(Paragraph(cur, p.page))
    chunks: list[TextChunk] = []
    cur_txt, pages = "", []
    for p in pieces:
        if cur_txt and len(cur_txt) + len(p.text) + 2 > max_chars:
            chunks.append(TextChunk(len(chunks), cur_txt, min(pages), max(pages)))
            cur_txt, pages = "", []
        cur_txt = f"{cur_txt}\n\n{p.text}".strip()
        pages.append(p.page)
    if cur_txt:
        chunks.append(TextChunk(len(chunks), cur_txt, min(pages), max(pages)))
    return chunks
