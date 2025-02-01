import random
from typing import List
from dria.utils.logging import logger
from dria.constants import COMPUTE_NODE_BATCH_SIZE


def select_nodes(node_scores, batch_size) -> List[str]:
    """
    Selects nodes based on their scores using weighted sampling.

    - If batch_size <= number of nodes, selection is without replacement.
    - If batch_size > number of nodes, selection is with replacement, allowing nodes to be selected multiple times.

    :param node_scores: List of dictionaries with 'score' and 'node' keys.
    :param batch_size: Number of nodes to select.
    :return: List of selected node addresses.
    """
    # Remove nodes with negative scores and warn about them
    valid_node_scores = {}
    for node, s in node_scores.items():
        if s < 0:
            # print(f"Warning: Node {item['node']} has a negative score and will be excluded.")
            pass
        else:
            valid_node_scores[node] = s

    # Check if there are valid nodes available
    if not valid_node_scores:
        logger.debug("No valid nodes available for selection.")
        return []

    # Extract nodes and their corresponding scores
    nodes = list(valid_node_scores.keys())
    scores = list(valid_node_scores.values())

    # Normalize the scores to sum to 1 (probabilities)
    total_score = sum(scores)
    if total_score == 0:
        # If all scores are zero, assign equal probability to all nodes
        probabilities = [1 / len(scores)] * len(scores)
    else:
        probabilities = [score / total_score for score in scores]

    if batch_size <= len(nodes):
        # Perform weighted sampling without replacement
        selected_nodes = []
        remaining_nodes = nodes.copy()
        remaining_probabilities = probabilities.copy()

        for _ in range(batch_size):
            if not remaining_nodes:
                break

            # Select a node based on the remaining probabilities
            chosen_node = random.choices(
                remaining_nodes, weights=remaining_probabilities, k=1
            )[0]
            logger.debug(
                f"Selected node: {chosen_node}, Score: {scores[nodes.index(chosen_node)]}"
            )
            selected_nodes.append(chosen_node)

            if selected_nodes.count(chosen_node) >= COMPUTE_NODE_BATCH_SIZE:
                # Remove the chosen node and its probability from the lists
                index = remaining_nodes.index(chosen_node)
                del remaining_nodes[index]
                del remaining_probabilities[index]

            # Re-normalize the probabilities if there are remaining nodes
            if remaining_nodes:  # Add check to prevent division by zero
                total_prob = sum(remaining_probabilities)
                if total_prob == 0:
                    # Assign equal probabilities if all remaining scores are zero
                    remaining_probabilities = [1 / len(remaining_probabilities)] * len(
                        remaining_probabilities
                    )
                else:
                    remaining_probabilities = [
                        p / total_prob for p in remaining_probabilities
                    ]
    else:
        # Perform weighted sampling with replacement
        selected_nodes = random.choices(nodes, weights=probabilities, k=batch_size)

    return selected_nodes
