import requests


def get_community_token() -> str:
    """Fetches and returns the URL from the API response."""
    response = requests.get("https://dkn.dria.co/auth/generate-token")
    if response.status_code == 200:
        return response.json()["data"][
            "auth_token"
        ]  # Assuming the response contains the URL as plain text
    else:
        raise Exception(f"Failed to fetch URL: {response.status_code}, {response.text}")
