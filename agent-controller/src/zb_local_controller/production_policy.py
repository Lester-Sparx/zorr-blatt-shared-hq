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


def compose_canon_prompt(canon_prompt: str, direction: str) -> str:
    canon = str(canon_prompt).strip()
    task_direction = str(direction).strip()
    if not canon or not task_direction:
        raise CanonPolicyError("SALVADOR_CANON_CONFLICT")
    lowered = task_direction.casefold()
    if any(phrase in lowered for phrase in _CONFLICT_PHRASES):
        raise CanonPolicyError("SALVADOR_CANON_CONFLICT")
    return (
        canon
        + "\n\nTASK-SPECIFIC LOCKED DIRECTION:\n"
        + task_direction
        + "\n\nThe task-specific direction may add detail but may not relax any immutable law above."
    )
