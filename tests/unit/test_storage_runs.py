import json
from assertllm.storage.runs import (
    config_to_folder,
    runs_dir_for_config,
    all_run_files,
    next_run_number,
    resolve_run_number,
    load_run,
    ensure_assertllm_gitignore
)


def test_config_to_folder_normalizes_special_chars():
    slug = config_to_folder("My Assertions v2.yaml")
    stem_part = slug.rsplit("-", 1)[0]
    assert stem_part == "my-assertions-v2"


def test_config_to_folder_is_deterministic():
    a = config_to_folder("examples/sample1.yaml")
    b = config_to_folder("examples/sample1.yaml")
    assert a == b


def test_config_to_folder_different_paths_same_stem_still_unique_by_hash():
    a = config_to_folder("examples/sample1.yaml")
    b = config_to_folder("other/sample1.yaml")
    assert a == b


def test_config_to_folder_empty_stem_falls_back():
    # stem is "---", which normalizes to an empty slug after stripping hyphens
    slug = config_to_folder("---.yaml")
    assert slug.startswith("config-")


def _write_run(config_path, n, isolated_cwd):
    runs_dir = runs_dir_for_config(config_path)
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / f"{n}.json").write_text(json.dumps({"run_id": n}))


def test_all_run_files_empty_when_no_dir(isolated_cwd):
    assert all_run_files("nope.yaml") == []


def test_all_run_files_sorted_ascending(isolated_cwd):
    for n in [3, 1, 2]:
        _write_run("sample.yaml", n, isolated_cwd)
    files = all_run_files("sample.yaml")
    assert [int(f.stem) for f in files] == [1, 2, 3]


def test_all_run_files_ignores_non_digit_json(isolated_cwd):
    _write_run("sample.yaml", 1, isolated_cwd)
    runs_dir = runs_dir_for_config("sample.yaml")
    (runs_dir / "notes.json").write_text("{}")
    files = all_run_files("sample.yaml")
    assert len(files) == 1


def test_next_run_number_starts_at_one(isolated_cwd):
    assert next_run_number("sample.yaml") == 1


def test_next_run_number_increments_from_max(isolated_cwd):
    _write_run("sample.yaml", 1, isolated_cwd)
    _write_run("sample.yaml", 5, isolated_cwd)
    assert next_run_number("sample.yaml") == 6


def test_resolve_run_number_positive_exact_match(isolated_cwd):
    _write_run("sample.yaml", 1, isolated_cwd)
    _write_run("sample.yaml", 2, isolated_cwd)
    resolved = resolve_run_number("sample.yaml", 2)
    assert resolved.stem == "2"


def test_resolve_run_number_negative_one_is_latest(isolated_cwd):
    _write_run("sample.yaml", 1, isolated_cwd)
    _write_run("sample.yaml", 2, isolated_cwd)
    _write_run("sample.yaml", 3, isolated_cwd)
    resolved = resolve_run_number("sample.yaml", -1)
    assert resolved.stem == "3"


def test_resolve_run_number_negative_two_is_second_latest(isolated_cwd):
    _write_run("sample.yaml", 1, isolated_cwd)
    _write_run("sample.yaml", 2, isolated_cwd)
    _write_run("sample.yaml", 3, isolated_cwd)
    resolved = resolve_run_number("sample.yaml", -2)
    assert resolved.stem == "2"


def test_resolve_run_number_zero_returns_none(isolated_cwd):
    _write_run("sample.yaml", 1, isolated_cwd)
    assert resolve_run_number("sample.yaml", 0) is None


def test_resolve_run_number_out_of_range_returns_none(isolated_cwd):
    _write_run("sample.yaml", 1, isolated_cwd)
    assert resolve_run_number("sample.yaml", 99) is None
    assert resolve_run_number("sample.yaml", -99) is None


def test_resolve_run_number_no_runs_returns_none(isolated_cwd):
    assert resolve_run_number("sample.yaml", -1) is None


def test_load_run_reads_json(isolated_cwd):
    _write_run("sample.yaml", 1, isolated_cwd)
    runs_dir = runs_dir_for_config("sample.yaml")
    record = load_run(runs_dir / "1.json")
    assert record["run_id"] == 1


def test_ensure_assertllm_gitignore_creates_dir_and_file(isolated_cwd):
    ensure_assertllm_gitignore()
    gitignore_path = isolated_cwd / ".assertllm" / ".gitignore"
    assert gitignore_path.exists()
    assert gitignore_path.read_text() == "*\n"


def test_ensure_assertllm_gitignore_does_not_overwrite_existing(isolated_cwd):
    assertllm_dir = isolated_cwd / ".assertllm"
    assertllm_dir.mkdir(parents=True)
    gitignore_path = assertllm_dir / ".gitignore"
    gitignore_path.write_text("custom content\n")
    ensure_assertllm_gitignore()
    assert gitignore_path.read_text() == "custom content\n"


def test_ensure_assertllm_gitignore_is_idempotent(isolated_cwd):
    ensure_assertllm_gitignore()
    ensure_assertllm_gitignore()
    gitignore_path = isolated_cwd / ".assertllm" / ".gitignore"
    assert gitignore_path.read_text() == "*\n"