from typing import Dict, Any


def recursive_variable_sampling(var, attribute_values: Dict[str, Dict[str, Any]]):
    sampler = var["sampler"]
    value = sampler()
    attr = {"name": var["name"], "description": var["description"], "value": value}
    attribute_values[var["name"]] = attr
    if "dependent_variables" in var:
        dependent_variables = var["dependent_variables"].get(value)
        if dependent_variables:
            for dependant_var in dependent_variables:
                recursive_variable_sampling(dependant_var, attribute_values)


def sample_variables(state: Dict[str, Any]):
    random_variables = state["random_variables"]
    n_samples = state.get("n_samples", 1)
    var_list = random_variables["random_variables"]
    sampled_features = []
    for _ in range(n_samples):
        attribute_values = {}
        for var in var_list:
            recursive_variable_sampling(var, attribute_values)
        sampled_features.append(attribute_values)
    return {"sampled_features": sampled_features}
