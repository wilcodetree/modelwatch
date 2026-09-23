import subprocess


def test_script_reads_value_with_pwsh() -> None:
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-File", "read-value.ps1"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "fixture-ready"
