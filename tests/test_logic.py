import numpy as np
import pytest

from app.services import grading, mastery
from app.services.retriever import cosine_similarity, retrieve
from app.database import SessionLocal


# ---- EMA mastery ---------------------------------------------------------------------------
def test_ema_first_attempt_uses_observed_performance():
    assert mastery.ema_update(None, 0.8) == 0.8
    assert mastery.ema_update(None, 0.0) == 0.0


def test_ema_formula_alpha_06():
    # A_new = 0.6 * latest + 0.4 * previous
    assert mastery.ema_update(0.5, 1.0) == pytest.approx(0.8)
    assert mastery.ema_update(0.8, 0.2) == pytest.approx(0.44)
    assert mastery.ema_update(0.2, 0.4) == pytest.approx(0.32)


def test_ema_rejects_out_of_range():
    with pytest.raises(ValueError):
        mastery.ema_update(0.5, 1.2)


@pytest.mark.parametrize("score,level", [(1.0, "good"), (0.80, "good"), (0.7999, "average"), (0.79, "average"),
                                         (0.50, "average"), (0.4999, "weak"), (0.0, "weak")])
def test_classification_boundaries(score, level):
    assert mastery.classify(score) == level


def test_classification_float_artifacts_at_boundary():
    assert mastery.classify(mastery.ema_update(0.8, 0.8)) == "good"   # 0.6*.8+0.4*.8 may be 0.79999..
    assert mastery.classify(mastery.ema_update(0.5, 0.5)) == "average"


# ---- grading ---------------------------------------------------------------------------------
KEY = {f"q{i}": {"correct": "A", "concept_id": "c1" if i < 4 else "c2"} for i in range(1, 6)}


def test_grading_and_score():
    g = grading.grade(KEY, {"q1": "A", "q2": "A", "q3": "B", "q4": "A", "q5": "C"})
    assert g["correct_count"] == 3 and g["total"] == 5 and g["score"] == 60.0


def test_concept_level_performance_groups_by_concept():
    g = grading.grade(KEY, {"q1": "A", "q2": "B", "q3": "A", "q4": "A", "q5": "B"})
    p = grading.concept_performance(g["per_question"])
    assert p["c1"]["performance"] == pytest.approx(2 / 3) and p["c1"]["had_incorrect"]   # q1-q3 belong to c1
    assert p["c2"]["performance"] == 0.5                                              # q4-q5 belong to c2


# ---- retrieval -------------------------------------------------------------------------------
def test_cosine_similarity_basic():
    q = np.array([1.0, 0.0])
    m = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]])
    assert cosine_similarity(q, m).tolist() == [1.0, 0.0, -1.0]


def test_retrieval_is_filtered_by_concept_metadata_before_ranking():
    with SessionLocal() as db:
        # query is about the cell membrane, but filtering to the homeostasis concept must win
        res = retrieve(db, "phospholipid bilayer channel proteins", concept_id="ch1-s1-c1")
        assert res and all(r.concept_id == "ch1-s1-c1" for r in res)
        res2 = retrieve(db, "phospholipid bilayer", chapter_id="ch2")
        assert all(r.chunk_id.startswith("ch2") for r in res2)


def test_retrieval_ranks_by_similarity():
    with SessionLocal() as db:
        res = retrieve(db, "negative feedback thermoregulation positive feedback childbirth", concept_id="ch1-s1-c1")
        assert res[0].score >= res[-1].score
        assert "feedback" in res[0].content.lower()


def test_retrieval_requires_a_filter():
    with SessionLocal() as db, pytest.raises(ValueError):
        retrieve(db, "anything")
