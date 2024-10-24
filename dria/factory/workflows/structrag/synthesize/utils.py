import re


def _extract_solution_order(text):
    # First try to find a line starting with a hyphen containing the ranking
    pattern1 = r'-\s*(.*?)\s*>\s*(.*?)\s*=\s*(.*?)\s*>\s*(.*?)\s*>\s*(.*?)(?:\s|$)'
    # Alternative pattern for other formats
    pattern2 = r'\*\*(.*?(?:>\s*|\=\s*).*?(?:>\s*|\=\s*).*?(?:>\s*|\=\s*).*?)\*\*'

    match = re.search(pattern1, text)
    if match:
        return [item.strip() for item in match.groups()]

    match = re.search(pattern2, text)
    if match:
        extracted_string = match.group(1)
        clean_pattern = r'\s*\(\d+\)'
        cleaned_string = re.sub(clean_pattern, '', extracted_string)
        return [s.strip() for s in re.split(r'[>=]', cleaned_string)]

    return None


def extract_solution_order(text):
    """
    Extracts solution rankings from text containing expressions like 'A > B = C > D'

    Args:
        text (str): The text containing the solution ranking

    Returns:
        list: List of lists containing solutions at the same rank level
    """

    # Find the content between <final_ranking> tags
    ranking_pattern = r'<final_ranking>\s*(.*?)\s*</final_ranking>'
    ranking_match = re.search(ranking_pattern, text, re.DOTALL)

    if not ranking_match:
        return None

    ranking_text = ranking_match.group(1).strip()

    # Split by '>' to get groups of solutions at different rank levels
    rank_groups = [group.strip() for group in ranking_text.split('>')]

    # For each rank group, split by '=' to get individual solutions
    parsed_ranks = []
    for group in rank_groups:
        solutions = [sol.strip() for sol in group.split('=')]
        if len(solutions) > 1:
            parsed_ranks += solutions
        else:
            parsed_ranks.append(solutions[0])

    return parsed_ranks


if __name__ == "__main__":
    # Example text input
    text = """
    ## Solution Analysis and Ranking:\n\nHere's a breakdown of each solution's effectiveness for this specific task:\n\n**1. Chunk:** While identifying relevant facts is a good starting point, this method relies heavily on finding specific information chunks about founding dates. This approach lacks structure and might struggle to find and connect the necessary information reliably.\n\n**2. Graph:** This method provides a clear visual representation of the relationships between entities. However, building a comprehensive knowledge graph can be complex and resource-intensive for a relatively simple task.\n\n**3. Table:** This approach offers a simple and efficient way to organize and access the necessary information. The table structure clearly links locations and their founding dates, making the calculation straightforward.\n\n**4. Algorithm:** This solution is highly effective and scalable. It leverages a database for efficient data retrieval and can be generalized to calculate the difference in founding dates for any two US locations.\n\n**5. Catalogue:** Similar to the table method, this approach offers a structured way to find information. However, navigating a hierarchical catalogue might be less efficient than directly accessing a table or querying a database.\n\n## Ranking:\n\nBased on the analysis above, the solutions are ranked as follows:\n\n**Algorithm (4) > Table (3) > Catalogue (5) > Graph (2) > Chunk (1)**\n\n**Explanation:**\n\n* **Algorithm (4) is the most effective** due to its efficiency, scalability, and ability to generalize to other similar tasks.\n* **Table (3) ranks second** for its simplicity and clear organization of relevant information.\n* **Catalogue (5) is slightly less efficient** than the table approach but still offers a structured way to access information.\n* **Graph (2), while visually appealing, is overly complex** for this specific task. \n* **Chunk (1) is the least effective** due to its lack of structure and potential difficulty in reliably finding and connecting information.
    """
    t = "## Solution Analysis and Ranking:\n\n**1. Chunk:** This approach is not suitable for the query.  Chunking is more useful for breaking down large amounts of text into manageable units.  It doesn't directly address the question of identifying the document that focuses on fluid behavior.\n\n**2. Graph:**  This approach could be effective.  By creating a graph with document nodes and edges representing relevant keywords like \"fluids,\" \"pressure,\" \"viscosity,\" \"buoyancy,\" etc., we can identify the document most connected to these concepts. This would likely be **Fluid Mechanics**.\n\n**3. Table:** This approach is similar to the graph method but presents the information in a tabular format.  The document with the most \"1\" values in the columns for fluid-related keywords would be the most relevant.  This would also likely point to **Fluid Mechanics**.\n\n**4. Algorithm:** This approach can be very effective if the algorithm is well-designed.  By defining rules based on keywords like \"fluid dynamics,\" \"pressure,\" \"flow,\" etc., we can accurately identify the document that best matches the query.  This would again likely point to **Fluid Mechanics**.\n\n**5. Catalogue:** This approach is less effective. While a catalogue could help organize the documents, it wouldn't provide a direct answer to the query.  It would require manually searching through the catalogue for the most relevant document.\n\n## Ranking:\n\nBased on the analysis above, here's the ranking of the solutions:\n\n**Algorithm > Graph = Table > Catalogue > Chunk** \n\n**Explanation:**\n\n* **Algorithm:** This is the most effective as it can be specifically tailored to identify the document with the highest relevance to the query.\n* **Graph & Table:** These approaches are similar in effectiveness and provide a good way to visualize the relationships between documents and keywords.\n* **Catalogue:** While useful for organization, it lacks the directness of other methods for answering the query.\n* **Chunk:** This approach is completely unsuitable for this task."
    t2 ="To determine the most suitable solution for answering the query, \"What are the key principles governing the behavior of fluids?\", let's compare and analyze each solution based on relevance:\n\n1. **Algorithm:** This solution can be used to score the importance of various physical laws related to fluid mechanics, such as Bernoulli's principle or the Navier-Stokes equations. It seems relevant to understanding fluid behavior but may not directly answer the query about key principles.\n\n2. **Table:** Creating a table with data on fluid mechanics topics could help organize information and identify relationships between different concepts. However, it might not effectively distill down to the core principles governing fluid behavior without deeper analysis.\n\n3. **Graph:** Representing fluid mechanics concepts as nodes in a graph can show relationships like cause-and-effect or hierarchical structure among principles. This method is useful for visualizing complex connections but may require additional steps to extract key principles from the graph's structure.\n\n4. **Catalogue:** Building a catalogue of fluid mechanics characteristics could organize principles into broad categories and specific details, making it easier to identify core concepts. However, its effectiveness depends on how well the catalogue captures the essence of fluid behavior principles.\n\n5. **Chunk:** Identifying and extracting segments related to fluid mechanics can provide straightforward answers but might not capture the comprehensive nature of key principles without additional analysis or comparison with other solutions.\n\nConsidering the query focuses on \"key principles governing the behavior of fluids,\" I would rank these solutions based on their relevance and effectiveness in delivering a direct answer:\n\n1. **Algorithm >** Catalogue: Both are powerful tools for organizing knowledge, but an algorithm specifically designed to score importance can more directly reveal key principles.\n2. **Catalogue =** Chunk: While a catalogue organizes concepts hierarchically, a chunk-based approach can effectively extract relevant segments of text focused on fluid mechanics. However, the effectiveness might vary based on how well these chunks are defined and extracted.\n3. **Table >** Graph: Both methods help organize data, but a table, when properly populated with relevant metrics or criteria for evaluating fluid behavior, can offer a clear comparison of principles.\n4. **Graph <** Algorithm: While graphs show relationships between concepts, they might require additional steps to directly answer the query about key principles governing fluid behavior.\n\nTherefore, the ranking from most suitable to least suitable based on relevance and effectiveness in answering \"What are the key principles governing the behavior of fluids?\" is:\n\n- Algorithm > Catalogue = Chunk > Table > Graph\n\nThis ranking indicates that using an algorithm specifically tailored for scoring importance in fluid mechanics knowledge would be the most effective approach to answer the query, followed closely by cataloging or chunking methods that focus on fluid mechanics."
    t3 = "## Solution Analysis and Ranking:\n\nThe query focuses on understanding the fundamental principles governing fluid behavior. This requires a deep understanding of the concepts within Fluid Mechanics. \n\nLet's analyze each solution's effectiveness:\n\n**1. Chunk:** This approach is not suitable for the query. While chunking is useful for organizing large amounts of information, it doesn't provide the specific knowledge required to understand fluid behavior. Chunking might help with general topics related to \"Fluid Mechanics\" but won't delve into the core principles.\n\n**2. Graph:** A graph structure could be helpful to visualize relationships between concepts within Fluid Mechanics. However, it would require significant effort to define nodes and edges accurately to represent the complex principles involved. While potentially useful, it's not the most direct or efficient solution for this query.\n\n**3. Table:** A table could effectively organize information related to different aspects of fluid behavior. It could list key principles, equations, and examples. This approach is quite suitable for presenting the core concepts in a structured manner.\n\n**4. Algorithm:** An algorithm using NLP and machine learning could potentially extract relevant concepts from the document \"Fluid Mechanics.\" However, this approach might struggle with the nuanced language used in scientific texts and could misinterpret the context of certain terms. While promising, it's not the most reliable solution for this query.\n\n**5. Catalogue:** A catalogue would provide a structured overview of the content in \"Fluid Mechanics.\" It could categorize principles, laws, and phenomena related to fluids. This approach offers a clear and organized way to access the necessary information.\n\n## Ranking:\n\nBased on the analysis, the ranking of the solutions is:\n\n**3 > 5 > 2 > 4 > 1**\n\n**Explanation:**\n\n* **Table (3)** is the most effective due to its direct and structured approach to presenting key concepts in fluid mechanics.\n* **Catalogue (5)** is a good alternative, providing a hierarchical organization of the content.\n* **Graph (2)** could be useful but requires significant effort for accurate representation.\n* **Algorithm (4)** has potential but faces challenges with interpreting scientific language.\n* **Chunk (1)** is the least effective as it doesn't provide the specific knowledge required."
    t4 = "<comparison_analysis>\nFor this specific query and document set, focusing on identifying \"key principles governing fluid behavior\":\n\n* **Algorithm:**  Could be tailored to identify documents with \"fluid\" and keywords related to principles (\"laws\", \"governing\", etc.). This offers a direct and potentially accurate approach.\n* **Catalogue:**  If well-structured, a catalogue could have a \"Physics\" category, with subcategories like \"Fluid Mechanics\" directly addressing the query. However, its effectiveness depends heavily on pre-existing catalogue structure. \n* **Table:**  Less effective. While it can identify documents containing \"fluid\", it's less suited to pinpoint those discussing \"key principles\" without complex keyword combinations. \n* **Graph:**  Similar to Table, it might link \"fluid\" to related concepts, but lacks the semantic understanding to specifically target \"key principles\".\n* **Chunk:** Least effective. Chunking helps with contextual understanding within a document but doesn't offer an efficient way to search across documents for this specific query.\n\n</comparison_analysis>\n\n<final_ranking>\nAlgorithm > Catalogue > Table > Graph > Chunk\n</final_ranking>"
    solution_order = extract_solution_order(t4)
    print(solution_order)