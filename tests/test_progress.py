import io
from datetime import UTC, datetime

import pytest

from maily.progress import ProgressReporter, format_eta


class _Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def _chunk(day: int) -> tuple[datetime, datetime]:
    start = datetime(2024, 1, day, tzinfo=UTC)
    end = datetime(2024, 1, day, 23, 59, 59, 999999, tzinfo=UTC)
    return start, end


def _stats(fetched=60, total=600, cached=12):
    return {"fetched": fetched, "total_fetched": total, "cached": cached}


def test_level1_reports_percentage_counts_and_date():
    stream = io.StringIO()
    reporter = ProgressReporter(level=1, stream=stream)
    reporter.update(10, 30, *_chunk(15), _stats())
    out = stream.getvalue().strip().splitlines()[-1]
    assert "Scanning: 37% complete" in out
    assert "Processing: 2024-01-15" in out
    assert "60/600 emails" in out


def test_level1_week_chunk_shows_date_range():
    stream = io.StringIO()
    reporter = ProgressReporter(level=1, stream=stream)
    start = datetime(2024, 1, 8, tzinfo=UTC)
    end = datetime(2024, 1, 14, 23, 59, 59, tzinfo=UTC)
    reporter.update(1, 4, start, end, _stats())
    assert "2024-01-08 to 2024-01-14" in stream.getvalue()


def test_level2_includes_rate_and_eta():
    clock = _Clock()
    stream = io.StringIO()
    reporter = ProgressReporter(level=2, stream=stream, clock=clock)
    clock.t = 0.0
    reporter.update(0, 30, *_chunk(1), _stats(fetched=60, total=60))
    clock.t = 300.0
    reporter.update(9, 30, *_chunk(10), _stats(fetched=60, total=600))
    out = stream.getvalue().strip().splitlines()[-1]
    assert "Scanning: 33% complete" in out
    assert "120/min" in out  # 600 emails in 5 minutes
    assert "~10min remaining" in out  # 20 chunks left at 30s each


def test_eta_updates_when_rate_changes():
    clock = _Clock()
    stream = io.StringIO()
    reporter = ProgressReporter(level=2, stream=stream, clock=clock)
    clock.t = 0.0
    reporter.update(0, 10, *_chunk(1), _stats(fetched=100, total=100))
    clock.t = 60.0
    reporter.update(4, 10, *_chunk(5), _stats(fetched=100, total=500))
    first_eta_line = stream.getvalue().strip().splitlines()[-1]
    clock.t = 120.0
    reporter.update(4, 10, *_chunk(5), _stats(fetched=100, total=500))
    second_eta_line = stream.getvalue().strip().splitlines()[-1]
    # 5 chunks in 60s => 12s/chunk => 5 remaining => ~1min
    assert "~1min remaining" in first_eta_line
    # Same chunk count in 120s => 24s/chunk => ~2min remaining
    assert "~2min remaining" in second_eta_line


def test_level3_includes_per_chunk_debug_line():
    stream = io.StringIO()
    reporter = ProgressReporter(level=3, stream=stream)
    reporter.update(0, 3, *_chunk(15), _stats(fetched=45, total=45, cached=12))
    out = stream.getvalue()
    assert "[2024-01-15] Fetched 45, Cached 12, Time:" in out
    assert "Scanning: 33% complete" in out


def test_invalid_level_raises():
    with pytest.raises(ValueError):
        ProgressReporter(level=9)


def test_format_eta_human_readable():
    assert format_eta(45) == "~45s remaining"
    assert format_eta(600) == "~10min remaining"
    assert format_eta(7500) == "~2h 5min remaining"
