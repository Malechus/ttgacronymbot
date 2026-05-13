import logging
import re
import threading

import praw
import praw.models

from .acronyms import AcronymStore
from .config import Config

logger = logging.getLogger(__name__)

_COMMAND_PATTERN = re.compile(r"!acronymbot\b", re.IGNORECASE)

_REPLY_TEMPLATE = """\
**Acronym{plural} detected:**

{definitions}

---
^(I am a bot \\| [Source / Feedback](https://www.reddit.com/r/TheTowerGame/))
"""

_NO_ACRONYMS_REPLY = """\
I couldn't find any known acronyms in that comment.

---
^(I am a bot \\| [Source / Feedback](https://www.reddit.com/r/TheTowerGame/))
"""


class AcronymBot:
    """
    Monitors r/TheTowerGame with two behaviors:

    - **Posts**: replies once to a new submission when acronyms are found in the title or body.
    - **Comments**: replies only when a user invokes ``!acronymbot``, scanning the parent
      comment (or post) for acronyms and replying to the invoking user.
    """

    def __init__(self, config: Config, store: AcronymStore) -> None:
        self._config = config
        self._store = store
        self._reddit = praw.Reddit(
            client_id=config.client_id,
            client_secret=config.client_secret,
            username=config.username,
            password=config.password,
            user_agent=config.user_agent,
        )
        self._replied_post_ids: set[str] = set()
        self._replied_comment_ids: set[str] = set()

    def run(self) -> None:
        """Stream submissions and comments concurrently. Runs indefinitely."""
        if self._config.dry_run:
            logger.info("*** DRY RUN MODE — no replies will be posted ***")
        logger.info("Monitoring r/%s...", self._config.subreddit)
        sub_thread = threading.Thread(
            target=self._stream_submissions, daemon=True, name="submissions"
        )
        comment_thread = threading.Thread(
            target=self._stream_comments, daemon=True, name="comments"
        )
        sub_thread.start()
        comment_thread.start()
        sub_thread.join()
        comment_thread.join()

    # ------------------------------------------------------------------
    # Stream workers
    # ------------------------------------------------------------------

    def _stream_submissions(self) -> None:
        subreddit = self._reddit.subreddit(self._config.subreddit)
        for submission in subreddit.stream.submissions(skip_existing=True):
            try:
                self._process_submission(submission)
            except Exception:
                logger.exception("Error processing submission %s", submission.id)

    def _stream_comments(self) -> None:
        subreddit = self._reddit.subreddit(self._config.subreddit)
        for comment in subreddit.stream.comments(skip_existing=True):
            try:
                self._process_comment(comment)
            except Exception:
                logger.exception("Error processing comment %s", comment.id)

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def _process_submission(self, submission: praw.models.Submission) -> None:
        """Reply once to a post if acronyms are found in its title or body."""
        if submission.id in self._replied_post_ids:
            return
        text = f"{submission.title} {submission.selftext}"
        found = self._store.find_in_text(text)
        if not found:
            return
        self._reply(submission, self._build_reply(found))
        self._replied_post_ids.add(submission.id)
        logger.info("Replied to post %s — matched: %s", submission.id, sorted(found.keys()))

    def _process_comment(self, comment: praw.models.Comment) -> None:
        """Reply to a user who invokes !acronymbot, scanning their parent for acronyms."""
        if not _COMMAND_PATTERN.search(comment.body):
            return
        if comment.id in self._replied_comment_ids:
            return
        if comment.author and comment.author.name.lower() == self._config.username.lower():
            return

        parent = comment.parent()
        if isinstance(parent, praw.models.Comment):
            parent_text = parent.body
        elif isinstance(parent, praw.models.Submission):
            parent_text = f"{parent.title} {parent.selftext}"
        else:
            return

        found = self._store.find_in_text(parent_text)
        self._replied_comment_ids.add(comment.id)

        if not found:
            self._reply(comment, _NO_ACRONYMS_REPLY.strip())
            logger.info("Replied to command in %s — no acronyms found", comment.id)
            return

        self._reply(comment, self._build_reply(found))
        logger.info("Replied to command in %s — matched: %s", comment.id, sorted(found.keys()))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_reply(self, found: dict[str, list[str]]) -> str:
        lines = []
        for k, defs in sorted(found.items()):
            if len(defs) == 1:
                lines.append(f"- **{k}** — {defs[0]}")
            else:
                sub = "\n".join(f"  {i}. {d}" for i, d in enumerate(defs, 1))
                lines.append(f"- **{k}**\n{sub}")
        plural = "s" if len(found) > 1 else ""
        return _REPLY_TEMPLATE.format(plural=plural, definitions="\n".join(lines)).strip()

    def _reply(self, target, body: str) -> None:
        """Post a reply, or log it without posting in dry-run mode."""
        if self._config.dry_run:
            logger.info("[DRY RUN] Would reply to %s:\n%s", getattr(target, "id", "?"), body)
            return
        target.reply(body)
