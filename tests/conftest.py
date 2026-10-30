import json
import os
import re
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))
_tmp = tempfile.mkdtemp(prefix="anatomind-test-")
os.environ["SECRET_KEY"] = "test-secret-key-test-secret-key-test-secret-key"
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["OLLAMA_MAX_RETRIES"] = "0"
os.environ["PDF_PATH"] = "/nonexistent.pdf"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Concept, TextbookChunk  # noqa: E402
from app.services import authentication, embeddings, ollama_client  # noqa: E402
from app.services.embeddings import to_bytes  # noqa: E402

DIM = 384


class FakeEmbedder:
    """Deterministic bag-of-words hashing embedder (384-d, L2-normalised)."""
    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(DIM, dtype=np.float32)
        for w in re.findall(r"[a-z]+", text.lower()):
            v[hash(w) % DIM] += 1.0
        n = np.linalg.norm(v)
        return v / n if n else v

    def embed_documents(self, texts, batch_size=32):
        return np.vstack([self._vec(t) for t in texts])

    def embed_query(self, text):
        return self._vec(text)


HOMEO = ("Homeostasis is the maintenance of stable internal conditions in the body. A set point is the target value "
         "of a physiological variable such as body temperature. Sensors detect deviations from the set point and the "
         "control center compares them with the set point before effectors act to restore balance. ")
FEEDBACK = ("Negative feedback reverses a deviation and returns the variable toward its set point, for example "
            "thermoregulation and blood glucose control. Positive feedback amplifies a change, as in childbirth, "
            "where oxytocin intensifies uterine contractions until delivery. ")
CELL = ("The cell membrane is a phospholipid bilayer that regulates the passage of ions and molecules. Channel proteins "
        "and carrier proteins move substances across the membrane by diffusion and active transport. ")


def _add_concept(db, cid, title, texts, ch="ch1", chnum=1):
    sec = f"{ch}-s1"
    db.add(Concept(id=cid, ordinal=int(cid[-1]), unit_id="unit1", unit_number=1, unit_title="Levels of Organization",
                   chapter_id=ch, chapter_number=chnum, chapter_title=f"Chapter {chnum}", section_id=sec,
                   section_number=f"{chnum}.1", section_title=f"Section {chnum}.1", concept_title=title,
                   page_start=10, page_end=12))
    db.flush()
    emb = FakeEmbedder()
    for i, t in enumerate(texts):
        db.add(TextbookChunk(id=f"{cid}#{i}", unit_id="unit1", unit_title="Levels of Organization", chapter_id=ch,
                             chapter_title=f"Chapter {chnum}", section_id=sec, section_title=f"Section {chnum}.1",
                             concept_id=cid, chunk_index=i, content=t, content_hash=str(hash(t)),
                             embedding=to_bytes(emb._vec(t)),
                             source_metadata={"source": "OpenStax Anatomy and Physiology 2e", "pdf_pages": [10 + i],
                                              "concept_title": title}))


class FakeLLM:
    def __init__(self):
        self.mode = "ok"
        self.calls = []

    def __call__(self, system, user, *, fmt=None, temperature=0.2, num_predict=2048):
        self.calls.append(user)
        if fmt is not None:                                    # quiz
            if self.mode == "bad_json":
                return "this is not json"
            n = int(re.search(r"Write exactly (\d+)", user).group(1))
            if self.mode == "few":
                n = min(n, 2)
            themes = ["set point", "sensors", "control center", "effectors", "stable internal conditions"]
            qs = []
            have = len(re.findall(r"^- ", user.split("Do not repeat these existing questions:")[1], re.M))
            for i in range(n):
                t = themes[(have + i) % 5]
                qs.append({"aspect": "basic", "question": f"Which description best matches the role of {t} "
                           f"in the textbook discussion number {have + i + 1}?",
                           "options": {"A": f"It relates to {t} in homeostasis and set point control",
                                       "B": "Storage of genetic information inside the nucleus",
                                       "C": "Production of antibodies by plasma cells",
                                       "D": "Absorption of nutrients across the intestinal villi"},
                           "correct": "A", "explanation": f"The excerpt describes {t}.", "source": "E1"})
            return json.dumps({"questions": qs})
        return ("## Topic Overview\n- **Homeostasis** keeps internal conditions stable [E1]. [E99]\n"
                "## Important Terms and Their Meanings\n- **Set point**: the target value of a variable [E1].\n" + "x" * 200)


@pytest.fixture(autouse=True)
def fresh_db(monkeypatch):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    embeddings.set_embedder(FakeEmbedder())
    authentication.reset_throttle()
    llm = FakeLLM()
    monkeypatch.setattr(ollama_client, "chat", llm)
    with SessionLocal() as db:
        _add_concept(db, "ch1-s1-c1", "Homeostasis", [HOMEO * 2, FEEDBACK * 2])
        _add_concept(db, "ch1-s1-c2", "Negative Feedback", [FEEDBACK * 3, HOMEO])
        _add_concept(db, "ch2-s1-c1", "Cell Membrane", [CELL * 4], ch="ch2", chnum=2)
        _add_concept(db, "ch2-s1-c3", "Tiny Topic", ["Too short."], ch="ch2", chnum=2)   # insufficient content
        db.commit()
    return llm


@pytest.fixture
def llm(fresh_db):
    return fresh_db


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


PASSWORD = "Str0ngPass1"


def make_user(client, email="alice@example.com", name="Alice Student"):
    r = client.post("/api/auth/signup", json={"full_name": name, "email": email, "password": PASSWORD,
                                              "confirm_password": PASSWORD})
    assert r.status_code == 201, r.text
    r = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()["user"]


@pytest.fixture
def user_client(client):
    make_user(client)
    return client


@pytest.fixture
def second_client():
    with TestClient(app) as c:
        make_user(c, "bob@example.com", "Bob Student")
        yield c
