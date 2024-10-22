import re


def extract_solution_order(text):
    pattern = r'\*\*(.*?>\s*.*?>\s*.*?>\s*.*?>\s*.*?)\*\*'
    match = re.search(pattern, text)

    if match:
        extracted_string = match.group(1)
        clean_pattern = r'\s*\(\d+\)'
        cleaned_string = re.sub(clean_pattern, '', extracted_string)

        return [s.strip() for s in cleaned_string.split(">")]
    else:
        return None


if __name__ == "__main__":
    # Example text input
    text = """
    ## Solution Analysis and Ranking:\n\nHere's a breakdown of each solution's effectiveness for this specific task:\n\n**1. Chunk:** While identifying relevant facts is a good starting point, this method relies heavily on finding specific information chunks about founding dates. This approach lacks structure and might struggle to find and connect the necessary information reliably.\n\n**2. Graph:** This method provides a clear visual representation of the relationships between entities. However, building a comprehensive knowledge graph can be complex and resource-intensive for a relatively simple task.\n\n**3. Table:** This approach offers a simple and efficient way to organize and access the necessary information. The table structure clearly links locations and their founding dates, making the calculation straightforward.\n\n**4. Algorithm:** This solution is highly effective and scalable. It leverages a database for efficient data retrieval and can be generalized to calculate the difference in founding dates for any two US locations.\n\n**5. Catalogue:** Similar to the table method, this approach offers a structured way to find information. However, navigating a hierarchical catalogue might be less efficient than directly accessing a table or querying a database.\n\n## Ranking:\n\nBased on the analysis above, the solutions are ranked as follows:\n\n**Algorithm (4) > Table (3) > Catalogue (5) > Graph (2) > Chunk (1)**\n\n**Explanation:**\n\n* **Algorithm (4) is the most effective** due to its efficiency, scalability, and ability to generalize to other similar tasks.\n* **Table (3) ranks second** for its simplicity and clear organization of relevant information.\n* **Catalogue (5) is slightly less efficient** than the table approach but still offers a structured way to access information.\n* **Graph (2), while visually appealing, is overly complex** for this specific task. \n* **Chunk (1) is the least effective** due to its lack of structure and potential difficulty in reliably finding and connecting information.
    """

    solution_order = extract_solution_order(text)
    print(solution_order)