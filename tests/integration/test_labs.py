from __future__ import annotations

from learning_plane.demo import DemoEnvironment


def test_all_labs_generate_evidence(tmp_path):
    root = tmp_path / "evidence"
    result = DemoEnvironment(root).all()
    assert set(result) == {"lab1", "lab2", "lab3", "lab4"}
    assert result["lab1"]["resumed"]["status"] == "completed"
    assert result["lab2"]["dataset_cases"] >= 80
    assert result["lab3"]["rollback"]["status"] == "rolled_back"
    assert result["lab4"]["idempotent_second_pass"] == []
    assert (root / "demo_all.json").exists()
