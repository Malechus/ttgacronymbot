import json
import re
from pathlib import Path


class AcronymStore:
    """Loads acronym definitions from a JSON file and finds them in text."""

    def __init__(self, path: str) -> None:
        self._acronyms: dict[str, str] = {}
        self.load(path)

    def load(self, path: str) -> None:
        """(Re)load acronyms from the given JSON file path."""
        data: dict[str, str] = json.loads(Path(path).read_text(encoding="utf-8"))
        self._acronyms = {k.upper(): v for k, v in data.items()}

    def find_in_text(self, text: str) -> dict[str, str]:
        """Return a mapping of every known acronym found as a whole word in text."""
        candidates = set(re.findall(r"\b[A-Z]{2,}\b", text.upper()))
        return {word: self._acronyms[word] for word in candidates if word in self._acronyms}

    def get(self, acronym: str) -> str | None:
        """Return the definition for a single acronym, or None if unknown."""
        return self._acronyms.get(acronym.upper())

    def __len__(self) -> int:
        return len(self._acronyms)

    def __contains__(self, acronym: str) -> bool:
        return acronym.upper() in self._acronyms
