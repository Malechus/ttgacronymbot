import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    client_id: str
    client_secret: str
    username: str
    password: str
    user_agent: str
    subreddit: str = "TheTowerGame"
    acronyms_file: str = "acronyms.json"
    dry_run: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            client_id=_require("REDDIT_CLIENT_ID"),
            client_secret=_require("REDDIT_CLIENT_SECRET"),
            username=_require("REDDIT_USERNAME"),
            password=_require("REDDIT_PASSWORD"),
            user_agent=os.environ.get("REDDIT_USER_AGENT", "ttgacronymbot/0.1.0"),
            subreddit=os.environ.get("SUBREDDIT", "TheTowerGame"),
            acronyms_file=os.environ.get("ACRONYMS_FILE", "acronyms.json"),
            dry_run=os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes"),
        )


def _require(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return value
