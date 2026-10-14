import hashlib
import json
from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verify_paper_snapshot', ROOT / 'scripts' / 'verify_paper_snapshot.py')
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)


def test_recorded_paper_artifacts_are_unchanged():
    assert snapshot.verify() == []


def test_integrity_check_rejects_changed_missing_and_added_files(tmp_path):
    (tmp_path / 'paper').mkdir()
    (tmp_path / 'results').mkdir()
    data = tmp_path / 'results' / 'original.json'
    data.write_text('original')
    manifest = {'frozen_roots': ['results'], 'files': {
        'results/original.json': hashlib.sha256(data.read_bytes()).hexdigest(),
    }}
    (tmp_path / 'paper' / 'manifest.json').write_text(json.dumps(manifest))
    assert snapshot.verify(tmp_path) == []
    data.write_text('changed')
    assert snapshot.verify(tmp_path) == ['changed: results/original.json']
    data.unlink()
    assert snapshot.verify(tmp_path) == ['missing: results/original.json']
    data.write_text('original')
    (tmp_path / 'results' / 'new.json').write_text('new')
    assert snapshot.verify(tmp_path) == ['unrecorded: results/new.json']
