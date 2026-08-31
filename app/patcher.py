
from pathlib import Path
import re

def validate_patch(patch: str) -> list[dict]:
    pattern = re.compile(
        r"FILE:\s*(?P<file>[^\n]+)\nOLD:\n(?P<old>.*?)\nEND_OLD\nNEW:\n(?P<new>.*?)\nEND_NEW",
        re.S,
    )
    changes = [m.groupdict() for m in pattern.finditer(patch or "")]
    if not changes:
        raise ValueError("Patch contains no valid FILE/OLD/NEW blocks")
    return changes

def apply_patch(repo_path: str, patch: str) -> list[str]:
    root = Path(repo_path).resolve()
    applied = []
    for change in validate_patch(patch):
        target = (root / change["file"]).resolve()
        if root not in target.parents:
            raise ValueError("Patch path escapes repository")
        if not target.exists():
            raise FileNotFoundError(change["file"])
        text = target.read_text(encoding="utf-8")
        old = change["old"]
        if old not in text:
            raise ValueError(f"OLD block not found in {change['file']}")
        target.write_text(text.replace(old, change["new"], 1), encoding="utf-8")
        applied.append(change["file"])
    return applied
