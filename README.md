# ttgacronymbot

A Reddit bot for [`r/TheTowerGame`](https://www.reddit.com/r/TheTowerGame/) that explains acronyms — automatically on new posts, and on-demand in comments via `!acronymbot`.

---

## How it works

The bot runs two concurrent streams:

| Trigger | Behavior |
|---|---|
| **New post** on r/TheTowerGame | Bot scans the title and body for known acronyms and replies **once** with definitions |
| **Comment containing `!acronymbot`** | Bot scans the **parent** comment (or post) for known acronyms and replies to the invoking user |

The bot never replies to its own comments, never replies to the same post or command twice, and in dry-run mode it logs what it *would* post without actually posting anything.

---

## Setup

### 1. Create a Reddit app

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click **"are you a developer? create an app..."**
3. Choose type **script**, give it a name, set redirect URI to `http://localhost:8080`
4. Note down the **client ID** (under the app name) and **client secret**

### 2. Create a bot Reddit account

Create a separate Reddit account for the bot (e.g. `u/TTGAcronymBot`) and note the username and password.

### 3. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=TTGAcronymBot
REDDIT_PASSWORD=your_bot_password
REDDIT_USER_AGENT=ttgacronymbot/0.1.0 by u/your_reddit_username

# Target subreddit — swap to your private sandbox sub for testing
SUBREDDIT=TheTowerGame

ACRONYMS_FILE=acronyms.json

# Set to true to log replies without posting them
DRY_RUN=false
```

### 4. Install

```bash
pip install -e ".[dev]"
```

### 5. Update acronyms

Edit `acronyms.json` to add or remove definitions. Keys are case-insensitive.

```json
{
  "DPS": "Damage Per Second",
  "HP": "Hit Points / Health Points",
  "OP": "Overpowered"
}
```

---

## Running

```bash
ttgacronymbot
```

Or directly:

```bash
python -m ttgacronymbot.main
```

---

## Configuration reference

All configuration is via environment variables (loaded from `.env` automatically):

| Variable | Required | Default | Description |
|---|---|---|---|
| `REDDIT_CLIENT_ID` | ✅ | — | Reddit app client ID |
| `REDDIT_CLIENT_SECRET` | ✅ | — | Reddit app client secret |
| `REDDIT_USERNAME` | ✅ | — | Bot account username |
| `REDDIT_PASSWORD` | ✅ | — | Bot account password |
| `REDDIT_USER_AGENT` | | `ttgacronymbot/0.1.0` | User-agent string sent to Reddit API |
| `SUBREDDIT` | | `TheTowerGame` | Subreddit to monitor (without `r/`) |
| `ACRONYMS_FILE` | | `acronyms.json` | Path to the acronym definitions file |
| `DRY_RUN` | | `false` | If `true`, log replies instead of posting them |

---

## Testing

### Unit tests

```bash
pytest -v
```

### Sandbox testing

Before running against `r/TheTowerGame`, test in a private subreddit:

1. Create a new subreddit, set visibility to **Private**
2. Add your bot account as a moderator or approved user
3. Set `SUBREDDIT=your_private_sub` in `.env`
4. Set `DRY_RUN=true` first — verify log output looks correct
5. Flip `DRY_RUN=false` to test actual posting in the sandbox
6. Once satisfied, set `SUBREDDIT=TheTowerGame` for production

---

## Project structure

```
ttgacronymbot/
├── .env.example               # credential template — copy to .env
├── .github/
│   └── copilot-instructions.md
├── acronyms.json              # acronym definitions
├── pyproject.toml
├── src/
│   └── ttgacronymbot/
│       ├── config.py          # Config dataclass, loaded from environment
│       ├── acronyms.py        # AcronymStore — load from JSON, find in text
│       ├── bot.py             # AcronymBot — submission + comment stream logic
│       └── main.py            # entry point
└── tests/
    ├── test_acronyms.py
    └── test_bot.py
```

---

## License

MIT — see [LICENSE](LICENSE)
