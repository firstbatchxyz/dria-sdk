import numpy as np

from dria.utils.logging import logger


def detect_outliers_iqr(data):
    """
    Detects outliers in the data using the IQR method.
    Returns the indices of outlier data points.
    """
    data_array = np.array(data)
    q1 = np.percentile(data_array, 25)
    q3 = np.percentile(data_array, 75)
    iqr = q3 - q1
    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)
    outliers = np.nonzero((data_array < lower_bound) | (data_array > upper_bound))
    return set(outliers[0]), lower_bound, upper_bound


def evaluate_nodes(task_data, previous_node_scores):
    """
    Evaluates nodes based on their performance metrics.
    Updates the node scores based on the current batch results.
    Returns the updated node scores.

    :param task_data: List of task results from the batch.
    :param previous_node_scores: Dictionary of previous node scores.
    :return: Updated dictionary of node scores.
    """
    # Initialize node scores with previous scores
    if previous_node_scores is None:
        node_scores = {t["node_address"]: 0.5 for t in task_data}
    else:
        node_scores = previous_node_scores.copy()

    # Extract performance metrics from all tasks
    execution_times = []
    roundtrip_times = []
    error_indices = set()
    for idx, task in enumerate(task_data):
        if task.get("error", False):
            error_indices.add(idx)
            continue
        execution_times.append(task["execution_time"])
        roundtrip_times.append(task["roundtrip"])

    # Check if we have any successful tasks
    if not execution_times or not roundtrip_times:
        logger.debug("No successful tasks in the batch. Skipping evaluation.")
        return node_scores

    # Detect outliers globally
    execution_outliers, exec_lower_bound, exec_upper_bound = detect_outliers_iqr(
        execution_times
    )
    roundtrip_outliers, rt_lower_bound, rt_upper_bound = detect_outliers_iqr(
        roundtrip_times
    )

    # Map indices to tasks for easy access
    index_task_map = {idx: task for idx, task in enumerate(task_data)}

    # Process each node
    for idx, task in index_task_map.items():
        node = task[
            "node_address"
        ]  # Replace 'model' with 'node' if you have node addresses
        if node not in node_scores:
            # Initialize node score if not present
            node_scores[node] = 0.5

        is_errored = task.get("error", False)

        if is_errored:
            # Apply error penalty
            node_scores[node] = max(node_scores[node] - 0.3, 0.0)
            logger.debug(
                f"Node {node} - Task {idx}: Error occurred. New Score: {node_scores[node]:.2f}"
            )
            continue
        # Check if the task is an outlier
        is_execution_outlier = idx in execution_outliers
        # is_roundtrip_outlier = idx in roundtrip_outliers

        if is_execution_outlier:
            # Apply penalty for outliers
            node_scores[node] = max(node_scores[node] - 0.1, 0.0)
            logger.debug(
                f"Node {node} - Task {idx}: Outlier detected. New Score: {node_scores[node]:.2f}"
            )
        else:
            # Reward for good performance
            node_scores[node] = min(node_scores[node] + 0.25, 1.0)
            logger.debug(
                f"Node {node} - Task {idx}: Good performance. New Score: {node_scores[node]:.2f}"
            )

    return node_scores
