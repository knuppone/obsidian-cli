from __future__ import annotations


class RestOnlyError(RuntimeError):
    def __init__(self, feature: str) -> None:
        super().__init__(
            f"{feature} requires --backend rest with Obsidian running and the "
            "Local REST API plugin enabled."
        )
        self.feature: str = feature
