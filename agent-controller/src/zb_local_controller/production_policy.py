from __future__ import annotations


class CanonPolicyError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


_CONFLICT_PHRASES = (
    "ignore canon",
    "ignore locked",
    "redesign the character",
    "redesign this character",
    "change the pose",
    "use a different pose",
    "generate the character from scratch",
    "text to image from scratch",
    "игнорируй канон",
    "игнорируй лок",
    "сделай редизайн",
    "измени позу",
    "смени позу",
    "сгенерируй персонажа с нуля",
)


_NEGATION_PREFIXES = (
    "do not",
    "don't",
    "never",
    "not",
    "не",
)


def _is_explicitly_negated(text: str, phrase_start: int) -> bool:
    prefix = text[:phrase_start].rstrip()
    return any(prefix.endswith(marker) for marker in _NEGATION_PREFIXES)


def _contains_affirmative_conflict(text: str) -> bool:
    for phrase in _CONFLICT_PHRASES:
        start = text.find(phrase)
        while start >= 0:
            if not _is_explicitly_negated(text, start):
                return True
            start = text.find(phrase, start + 1)
    return False


def compose_canon_prompt(canon_prompt: str, direction: str) -> str:
    canon = str(canon_prompt).strip()
    task_direction = str(direction).strip()
    if not canon or not task_direction:
        raise CanonPolicyError("SALVADOR_CANON_CONFLICT")
    lowered = task_direction.casefold()
    if _contains_affirmative_conflict(lowered):
        raise CanonPolicyError("SALVADOR_CANON_CONFLICT")
    return (
        canon
        + "\n\nTASK-SPECIFIC LOCKED DIRECTION:\n"
        + task_direction
        + "\n\nThe task-specific direction may add detail but may not relax any immutable law above."
    )
