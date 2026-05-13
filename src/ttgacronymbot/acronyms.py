import json
import re
from pathlib import Path


def _strip_jsonc_comments(text: str) -> str:
    """Strip // line comments and /* */ block comments from JSONC text."""
    result: list[str] = []
    i = 0
    in_string = False
    while i < len(text):
        if in_string:
            if text[i] == "\\":
                result.append(text[i : i + 2])
                i += 2
                continue
            elif text[i] == '"':
                in_string = False
            result.append(text[i])
        else:
            if text[i] == '"':
                in_string = True
                result.append(text[i])
            elif text[i : i + 2] == "//":
                while i < len(text) and text[i] != "\n":
                    i += 1
                continue
            elif text[i : i + 2] == "/*":
                end = text.find("*/", i + 2)
                i = end + 2 if end != -1 else len(text)
                continue
            else:
                result.append(text[i])
        i += 1
    return "".join(result)


class AcronymStore:
    """Loads acronym definitions from a JSONC file and finds them in text."""

    def __init__(self, path: str) -> None:
        self._acronyms: dict[str, str] = {}
        self.load(path)

    def load(self, path: str) -> None:
        """(Re)load acronyms from the given JSONC file path."""
        raw = Path(path).read_text(encoding="utf-8")
        data: dict[str, str] = json.loads(_strip_jsonc_comments(raw))
        self._acronyms = dict(data)

    def find_in_text(self, text: str) -> dict[str, str]:
        """Return a mapping of every known acronym found as a whole word in text (case-sensitive)."""
        candidates = set(re.findall(r"[A-Za-z]\w*%?", text))
        return {word: self._acronyms[word] for word in candidates if word in self._acronyms}

    def get(self, acronym: str) -> str | None:
        """Return the definition for a single acronym, or None if unknown."""
        return self._acronyms.get(acronym)

    def __len__(self) -> int:
        return len(self._acronyms)

    def __contains__(self, acronym: str) -> bool:
        return acronym in self._acronyms
