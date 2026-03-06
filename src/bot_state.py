from enum import Enum, auto


class TopState(Enum):
    """
    Top-level FSM for the 띵타이쿤 fishing minigame automation.

    IDLE      → Waiting for a minigame UI to appear
    CLASSIFY  → Minigame UI detected; determining which game (A/B/C)
    GAME_A    → Executing minigame A (timing right-click)
    GAME_B    → Executing minigame B (gauge control)
    GAME_C    → Executing minigame C (cursor PID tracking)
    COOLDOWN  → Post-game cooldown before returning to IDLE
    """
    IDLE = auto()
    CLASSIFY = auto()
    GAME_A = auto()
    GAME_B = auto()
    GAME_C = auto()
    COOLDOWN = auto()


class GameResult(Enum):
    """Return value from each game module's tick() function."""
    RUNNING = auto()   # Game is still in progress
    SUCCESS = auto()   # Game completed successfully
    FAILED = auto()    # Game failed or UI disappeared
