import tempfile
from pathlib import Path
from maily.db import Database
from maily.tui import grouped_rows


def test_database_summary_cache():
    """Test that email summaries can be cached and retrieved from the database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    try:
        db = Database(db_path)
        
        db.store_summary("test-msg-1", "Test summary", "test-model", "test-fingerprint")
        cached = db.get_summary("test-msg-1", "test-fingerprint")
        assert cached == "Test summary"
        
        db.store_summary("test-msg-1", "Updated summary", "test-model-2", "different-fingerprint")
        cached = db.get_summary("test-msg-1", "different-fingerprint")
        assert cached == "Updated summary"
        
        cached = db.get_summary("nonexistent", "fingerprint")
        assert cached is None
        
        db.close()
    finally:
        db_path.unlink()


def test_grouped_rows_preserves_order():
    """Test that grouped_rows preserves the original order for each category."""
    rows = [
        {"category": "Work", "subject": "Older", "last_received_at": "2026-08-25T08:00:00", "importance": 1},
        {"category": "Work", "subject": "Newer", "last_received_at": "2026-08-25T09:00:00", "importance": 2},
        {"category": "Personal", "subject": "Test", "last_received_at": "2026-08-25T10:00:00", "importance": 3},
    ]
    grouped = grouped_rows(rows, ["Work", "Personal"])
    
    assert [row["subject"] for row in grouped["Work"]] == ["Newer", "Older"]
    assert [row["subject"] for row in grouped["Personal"]] == ["Test"]


def test_grouped_rows_handles_empty_categories():
    """Test that grouped_rows handles empty categories correctly."""
    rows = [
        {"category": "Work", "subject": "Test", "last_received_at": "2026-08-25T08:00:00", "importance": 1},
    ]
    grouped = grouped_rows(rows, ["Work", "Personal", "Other"])
    
    assert [row["subject"] for row in grouped["Work"]] == ["Test"]
    assert grouped["Personal"] == []
    assert grouped["Other"] == []


def test_grouped_rows_handles_empty_body():
    """Test that grouped_rows handles rows with empty body."""
    rows = [
        {"category": "Work", "subject": "Test", "body": "", "last_received_at": "2026-08-25T08:00:00", "importance": 1},
    ]
    grouped = grouped_rows(rows, ["Work", "Personal"])
    
    assert [row["subject"] for row in grouped["Work"]] == ["Test"]
    assert grouped["Personal"] == []
