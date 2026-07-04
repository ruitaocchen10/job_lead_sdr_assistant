from pathlib import Path

PROFILE_PATH = Path("context/profile.md")


def load_profile() -> str:
    if not PROFILE_PATH.exists():
        raise FileNotFoundError(
            f"User profile not found at {PROFILE_PATH}. "
            "Create it using context/profile.md as a template."
        )
    return PROFILE_PATH.read_text()
