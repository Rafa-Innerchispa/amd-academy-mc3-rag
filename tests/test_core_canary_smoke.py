"""Golden-flow temporal canary smoke test."""

def test_temporal_canary_marker_optional():
    from pathlib import Path
    docs = Path("docs")
    assert docs.is_dir()
