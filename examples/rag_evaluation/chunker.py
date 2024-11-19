from typing import List
from pathlib import Path
from collections import defaultdict
import re


class ReadmeChunker:
    """A class to chunk markdown files based on headers."""

    def __init__(self, docs_dir: str, min_chunk_size: int = 500):
        """
        Initialize the ReadmeChunker.

        Args:
            docs_dir (str): Directory containing markdown files
            min_chunk_size (int): Minimum size of chunks in characters
        """
        self.docs_dir = Path(docs_dir)
        self.min_chunk_size = min_chunk_size
        self.chunks = self._process_markdown_files()

    def _process_markdown_files(self) -> List[dict]:
        """Process all markdown files in the directory."""
        all_chunks = []

        try:
            for file_path in self.docs_dir.rglob("*.md"):
                chunks = self._process_single_file(file_path)
                all_chunks.extend(chunks)

            return all_chunks

        except Exception as e:
            raise Exception(f"Error processing markdown files: {str(e)}")

    def _process_single_file(self, file_path: Path) -> List[dict]:
        """
        Process a single markdown file.

        Args:
            file_path (Path): Path to the markdown file

        Returns:
            List[str]: List of chunks from the file
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                return [
                    {"chunk": ch, "path": file_path}
                    for ch in self._chunk_by_headers(content)
                ]

        except Exception as e:
            print(f"Warning: Could not process {file_path}: {str(e)}")
            return []

    def _chunk_by_headers(self, markdown_text: str) -> List[str]:
        """
        Split markdown text into chunks based on headers.

        Args:
            markdown_text (str): The markdown text to chunk

        Returns:
            List[str]: List of text chunks
        """
        header_pattern = r"^#{1,6}\s.*$"
        chunks = []
        current_chunk = []
        current_size = 0

        for line in markdown_text.split("\n"):
            if re.match(header_pattern, line) and current_size > self.min_chunk_size:
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_size = len(line)
            else:
                current_chunk.append(line)
                current_size += len(line) + 1

        # Add the last chunk if it exists
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def get_chunks(self):
        """
        Get RAG chunks
        Returns:

        """
        return self.chunks

    def get_files(self):
        """
        Get files, less granular than chunks
        Returns:

        """
        chunks = self.get_chunks()
        files = defaultdict(list)
        for chunk in chunks:
            files[str(chunk["path"])].append(chunk["chunk"])
        return ["\n".join(v) for k, v in files.items()]
