import json
import pytest
from unittest.mock import MagicMock, patch
import praw.models
from ttgacronymbot.bot import AcronymBot
from ttgacronymbot.config import Config
from ttgacronymbot.acronyms import AcronymStore


@pytest.fixture
def acronyms_file(tmp_path):
    data = {"DPS": "Damage Per Second", "HP": "Hit Points"}
    p = tmp_path / "acronyms.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


@pytest.fixture
def config(acronyms_file):
    return Config(
        client_id="id",
        client_secret="secret",
        username="testbot",
        password="pass",
        user_agent="testbot/0.1",
        subreddit="TheTowerGame",
        acronyms_file=acronyms_file,
    )


@pytest.fixture
def store(acronyms_file):
    return AcronymStore(acronyms_file)


def _make_bot(config, store):
    with patch("praw.Reddit"):
        return AcronymBot(config, store)


def _make_submission(sub_id="post123", title="DPS guide", selftext=""):
    submission = MagicMock(spec=praw.models.Submission)
    submission.id = sub_id
    submission.title = title
    submission.selftext = selftext
    return submission


def _make_comment(comment_id="cmt123", body="!acronymbot", author_name="someuser"):
    comment = MagicMock()
    comment.id = comment_id
    comment.body = body
    comment.author.name = author_name
    return comment


def _make_parent_comment(body="The DPS is amazing"):
    parent = MagicMock(spec=praw.models.Comment)
    parent.body = body
    return parent


# ---------------------------------------------------------------------------
# Submission tests
# ---------------------------------------------------------------------------

def test_bot_replies_to_post_when_acronyms_found(config, store):
    bot = _make_bot(config, store)
    submission = _make_submission(title="Check out this DPS build")

    bot._process_submission(submission)

    submission.reply.assert_called_once()
    reply_text = submission.reply.call_args[0][0]
    assert "DPS" in reply_text
    assert "Damage Per Second" in reply_text


def test_bot_does_not_reply_to_post_without_acronyms(config, store):
    bot = _make_bot(config, store)
    submission = _make_submission(title="Check out this cool build")

    bot._process_submission(submission)

    submission.reply.assert_not_called()


def test_bot_does_not_reply_to_same_post_twice(config, store):
    bot = _make_bot(config, store)
    submission = _make_submission(title="DPS tips")

    bot._process_submission(submission)
    bot._process_submission(submission)

    assert submission.reply.call_count == 1


def test_bot_scans_selftext_as_well_as_title(config, store):
    bot = _make_bot(config, store)
    submission = _make_submission(title="My build", selftext="The HP is really low here")

    bot._process_submission(submission)

    submission.reply.assert_called_once()
    assert "HP" in submission.reply.call_args[0][0]


def test_bot_post_reply_uses_plural_for_multiple_acronyms(config, store):
    bot = _make_bot(config, store)
    submission = _make_submission(title="DPS and HP guide")

    bot._process_submission(submission)

    assert "Acronyms detected" in submission.reply.call_args[0][0]


def test_bot_post_reply_uses_singular_for_one_acronym(config, store):
    bot = _make_bot(config, store)
    submission = _make_submission(title="A DPS guide")

    bot._process_submission(submission)

    reply_text = submission.reply.call_args[0][0]
    assert "Acronym detected" in reply_text
    assert "Acronyms detected" not in reply_text


# ---------------------------------------------------------------------------
# Comment / !acronymbot command tests
# ---------------------------------------------------------------------------

def test_bot_ignores_comment_without_command(config, store):
    bot = _make_bot(config, store)
    comment = _make_comment(body="The DPS is great")

    bot._process_comment(comment)

    comment.reply.assert_not_called()


def test_bot_replies_to_command_with_parent_acronyms(config, store):
    bot = _make_bot(config, store)
    parent = _make_parent_comment("The DPS is insane")
    comment = _make_comment(body="!acronymbot what does this mean?")
    comment.parent.return_value = parent

    bot._process_comment(comment)

    comment.reply.assert_called_once()
    reply_text = comment.reply.call_args[0][0]
    assert "DPS" in reply_text
    assert "Damage Per Second" in reply_text


def test_bot_replies_no_acronyms_found_when_parent_has_none(config, store):
    bot = _make_bot(config, store)
    parent = _make_parent_comment("Nothing special here")
    comment = _make_comment(body="!acronymbot")
    comment.parent.return_value = parent

    bot._process_comment(comment)

    comment.reply.assert_called_once()
    assert "couldn't find" in comment.reply.call_args[0][0].lower()


def test_bot_does_not_reply_to_own_command_comments(config, store):
    bot = _make_bot(config, store)
    comment = _make_comment(body="!acronymbot", author_name="testbot")

    bot._process_comment(comment)

    comment.reply.assert_not_called()


def test_bot_does_not_reply_twice_to_same_command_comment(config, store):
    bot = _make_bot(config, store)
    parent = _make_parent_comment("The DPS is great")
    comment = _make_comment(body="!acronymbot")
    comment.parent.return_value = parent

    bot._process_comment(comment)
    bot._process_comment(comment)

    assert comment.reply.call_count == 1


def test_bot_command_is_case_insensitive(config, store):
    bot = _make_bot(config, store)
    parent = _make_parent_comment("The HP is low")
    comment = _make_comment(body="!AcronymBot what does HP mean?")
    comment.parent.return_value = parent

    bot._process_comment(comment)

    comment.reply.assert_called_once()


def test_bot_command_scans_parent_submission(config, store):
    bot = _make_bot(config, store)
    parent = MagicMock(spec=praw.models.Submission)
    parent.title = "All about HP"
    parent.selftext = ""
    comment = _make_comment(body="!acronymbot")
    comment.parent.return_value = parent

    bot._process_comment(comment)

    comment.reply.assert_called_once()
    assert "HP" in comment.reply.call_args[0][0]


def test_bot_command_reply_lists_all_found_acronyms(config, store):
    bot = _make_bot(config, store)
    parent = _make_parent_comment("Check the DPS and HP values")
    comment = _make_comment(body="!acronymbot")
    comment.parent.return_value = parent

    bot._process_comment(comment)

    reply_text = comment.reply.call_args[0][0]
    assert "DPS" in reply_text
    assert "HP" in reply_text


# ---------------------------------------------------------------------------
# Dry-run mode tests
# ---------------------------------------------------------------------------

def _make_dry_run_bot(config, store):
    dry_config = Config(
        client_id=config.client_id,
        client_secret=config.client_secret,
        username=config.username,
        password=config.password,
        user_agent=config.user_agent,
        subreddit=config.subreddit,
        acronyms_file=config.acronyms_file,
        dry_run=True,
    )
    with patch("praw.Reddit"):
        return AcronymBot(dry_config, store)


def test_dry_run_does_not_post_reply_to_submission(config, store):
    bot = _make_dry_run_bot(config, store)
    submission = _make_submission(title="A great DPS guide")

    bot._process_submission(submission)

    submission.reply.assert_not_called()


def test_dry_run_does_not_post_reply_to_command_comment(config, store):
    bot = _make_dry_run_bot(config, store)
    parent = _make_parent_comment("The DPS is high")
    comment = _make_comment(body="!acronymbot")
    comment.parent.return_value = parent

    bot._process_comment(comment)

    comment.reply.assert_not_called()


def test_dry_run_still_tracks_replied_ids(config, store):
    """Dry-run deduplication should work the same as live mode."""
    bot = _make_dry_run_bot(config, store)
    submission = _make_submission(title="DPS guide")

    bot._process_submission(submission)
    bot._process_submission(submission)

    # reply was never called, but the ID was still tracked so no double-processing
    assert submission.id in bot._replied_post_ids
