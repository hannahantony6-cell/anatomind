from pydantic import BaseModel


class ConceptOut(BaseModel):
    id: str
    title: str
    ordinal: int
    chunk_count: int
    char_count: int
    available: bool          # enough indexed textbook text to support AI generation


class SectionOut(BaseModel):
    id: str
    number: str
    title: str
    concepts: list[ConceptOut] = []


class ChapterOut(BaseModel):
    id: str
    number: int
    title: str
    sections: list[SectionOut] = []


class UnitOut(BaseModel):
    id: str
    number: int
    title: str
    chapters: list[ChapterOut] = []


class FlatSectionOut(BaseModel):
    id: str
    number: str
    title: str
    chapter_id: str


class FlatChapterOut(BaseModel):
    id: str
    number: int
    title: str
    unit_id: str


class FlatUnitOut(BaseModel):
    id: str
    number: int
    title: str


class ConceptDetail(BaseModel):
    id: str
    title: str
    unit_id: str
    unit_title: str
    chapter_id: str
    chapter_number: int
    chapter_title: str
    section_id: str
    section_number: str
    section_title: str
    page_start: int | None = None
    page_end: int | None = None
    chunk_count: int
    available: bool
