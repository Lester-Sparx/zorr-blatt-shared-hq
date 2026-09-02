from zb_local_controller.__main__ import RETIRED_CODE, main


def test_execution_entrypoint_is_retired_fail_closed(capsys):
    exit_code = main(["--once"])
    captured = capsys.readouterr()
    assert exit_code != 0
    assert RETIRED_CODE in captured.err


def test_injected_legacy_factories_do_not_reactivate_execution(capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("retired execution dependency must not be initialized")

    exit_code = main(["--once"], github_factory=forbidden, backend_factory=forbidden)
    captured = capsys.readouterr()
    assert exit_code != 0
    assert RETIRED_CODE in captured.err
