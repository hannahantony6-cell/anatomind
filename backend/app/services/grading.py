"""Deterministic grading. The LLM is never consulted."""


def grade(answer_key: dict, selected: dict[str, str]) -> dict:
    """answer_key: {qid: {"correct": "B", "concept_id": ...}};  selected: {qid: "B"}."""
    per_question = {}
    correct_count = 0
    for qid, key in answer_key.items():
        chosen = selected.get(qid)
        ok = chosen is not None and chosen == key["correct"]
        correct_count += int(ok)
        per_question[qid] = {"selected": chosen, "correct": key["correct"], "is_correct": ok,
                             "concept_id": key["concept_id"]}
    total = len(answer_key)
    score = round(correct_count / total * 100, 2) if total else 0.0
    return {"correct_count": correct_count, "total": total, "score": score, "per_question": per_question}


def concept_performance(per_question: dict) -> dict[str, dict]:
    """Group results by concept -> {correct, total, performance(0-1), had_incorrect}."""
    out: dict[str, dict] = {}
    for r in per_question.values():
        c = out.setdefault(r["concept_id"], {"correct": 0, "total": 0})
        c["total"] += 1
        c["correct"] += int(r["is_correct"])
    for c in out.values():
        c["performance"] = c["correct"] / c["total"]
        c["had_incorrect"] = c["correct"] < c["total"]
    return out
