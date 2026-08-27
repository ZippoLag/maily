from __future__ import annotations

import sys
import time
from datetime import datetime

LEVELS = (1, 2, 3)


def format_eta(seconds: float) -> str:
    """Format a duration in seconds as a compact remaining-time label."""
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"~{seconds}s remaining"
    minutes = seconds // 60
    if minutes < 60:
        return f"~{minutes}min remaining"
    hours = minutes // 60
    return f"~{hours}h {minutes % 60}min remaining"


class ProgressReporter:
    """Render scan progress lines to a stream at a configurable verbosity.

    Level 1 (default)::

        Scanning: 35% complete (Processing: 2024-01-15, 450/1287 emails)

    Level 2 (verbose) appends the processing rate and ETA::

        Scanning: 35% complete (Processing: 2024-01-15, 450/1287 emails, 120/min, ~6min remaining)

    Level 3 (debug) prefixes a per-chunk detail line::

        [2024-01-15] Fetched 45, Cached 12, Time: 2.3s
        Scanning: 35% complete ...

    Progress is written to ``sys.stderr`` by default so stdout (e.g. JSON
    output) stays clean.
    """

    def __init__(self, level: int = 1, stream=None, clock=time.monotonic):
        if level not in LEVELS:
            raise ValueError(
                f"Invalid progress level: {level} (expected one of {LEVELS})"
            )
        self.level = level
        self.stream = stream if stream is not None else sys.stderr
        self._clock = clock
        self._started = clock()
        self._last = self._started

    def update(
        self,
        chunk_index: int,
        total_chunks: int,
        chunk_start: datetime,
        chunk_end: datetime,
        stats: dict | None = None,
    ) -> None:
        """Report progress for one processed chunk."""
        stats = stats or {}
        now = self._clock()
        elapsed = now - self._started
        chunk_time = now - self._last
        self._last = now
        percent = round((chunk_index + 1) / total_chunks * 100) if total_chunks else 100
        fetched = stats.get("fetched", 0)
        total_fetched = stats.get("total_fetched", 0)
        label = _chunk_label(chunk_start, chunk_end)
        line = (
            f"Scanning: {percent}% complete "
            f"(Processing: {label}, {fetched}/{total_fetched} emails)"
        )
        if self.level >= 2:
            rate_per_min = total_fetched / (elapsed / 60) if elapsed > 0 else 0.0
            eta = _eta_seconds(elapsed, chunk_index, total_chunks)
            line += f", {rate_per_min:.0f}/min, {format_eta(eta)}"
        if self.level >= 3:
            self.stream.write(
                f"[{chunk_start.date().isoformat()}] Fetched {fetched}, "
                f"Cached {stats.get('cached', 0)}, Time: {chunk_time:.1f}s\n"
            )
        self.stream.write(line + "\n")
        self.stream.flush()


def _chunk_label(chunk_start: datetime, chunk_end: datetime) -> str:
    if chunk_start.date() == chunk_end.date():
        return chunk_start.date().isoformat()
    return f"{chunk_start.date().isoformat()} to {chunk_end.date().isoformat()}"


def _eta_seconds(elapsed: float, chunk_index: int, total_chunks: int) -> float:
    processed = chunk_index + 1
    remaining = max(0, total_chunks - processed)
    if processed <= 0 or elapsed <= 0 or remaining <= 0:
        return 0.0
    return elapsed / processed * remaining
