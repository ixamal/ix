from pathlib import Path

from ix_crate.paths import APPLE_MUSIC, STEMS_AUDIO


class CrateSafetyError(PermissionError):
    pass


def assert_under_stems(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    root = STEMS_AUDIO.expanduser().resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise CrateSafetyError(f"Refusing path outside stems_audio: {path}") from exc
    apple = APPLE_MUSIC.expanduser()
    if apple.exists():
        try:
            resolved.relative_to(apple.resolve())
        except ValueError:
            pass
        else:
            raise CrateSafetyError("Refusing to touch Apple Music Media.localized.")
    return resolved
