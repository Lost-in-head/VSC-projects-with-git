from src.main import main


def test_full_cli_pipeline(capsys):
    payload = main()
    assert payload is not None

    captured = capsys.readouterr()
    assert "Success! Your listing draft is ready" in captured.out
