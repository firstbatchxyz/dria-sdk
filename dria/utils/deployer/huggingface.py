import os
from typing import Optional
from huggingface_hub import HfApi, create_repo
from datasets import Dataset


class HuggingFaceDeployer:
    """Class for deploying datasets to the HuggingFace Hub."""

    def __init__(self, token: Optional[str] = None):
        """
        Initialize the HuggingFace deployer.

        Args:
            token (Optional[str]): HuggingFace API token. If not provided, the 'HF_TOKEN' environment variable is used.
        """
        self.token = token or os.environ.get("HF_TOKEN")
        if not self.token:
            raise ValueError(
                "HuggingFace token must be provided or set in HF_TOKEN env var"
            )
        self.api = HfApi(token=self.token)

    def deploy(self, dataset: Dataset, repo_name: str, private: bool = False) -> str:
        """
        Deploy a HuggingFace dataset to the HuggingFace Hub.

        Args:
            dataset (Dataset): The dataset to deploy.
            repo_name (str): The repository name to create or update.
            private (bool): Whether the repository should be private.

        Returns:
            str: The URL of the deployed dataset.
        """

        # Create or retrieve the repository
        try:
            repo = create_repo(
                repo_id=repo_name,
                token=self.token,
                private=private,
                repo_type="dataset",
                exist_ok=True,
            )
            repo_id = repo.repo_id
        except Exception as error:
            raise RuntimeError(f"Failed to create or retrieve repository: {error}")

        # Upload the dataset to the Hub
        try:
            dataset.push_to_hub(repo_id=repo_id, token=self.token, private=private)
        except Exception as error:
            raise RuntimeError(f"Failed to push dataset: {error}")

        return f"https://huggingface.co/datasets/{repo_id}"
