from greet import main, parser


def test_uppercase_flag_is_documented() -> None:
    assert "--uppercase" in parser().format_help()


def test_uppercase_flag_changes_output(capsys) -> None:
    assert main(["Ada", "--uppercase"]) == "HELLO, ADA!"
    assert capsys.readouterr().out == "HELLO, ADA!\n"
