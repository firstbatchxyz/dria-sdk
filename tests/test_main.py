from dria.factory import score_complexity, evolve_complexity, generate_semantic_triple


if __name__ == "__main__":
    workflow = generate_semantic_triple(unit="sentence", language="en", high_score=5, low_score=1, difficulty="college")
    print(workflow.model_dump_json(exclude_none=True, exclude_unset=True, by_alias=True, indent=2))