#
from interlinked import Workflow

wkf = Workflow("test-mutate")


@wkf.mutate(prefix=lambda prefix: prefix.upper())
@wkf.provide('{prefix}.echo')
@wkf.mutate(suffix=lambda prefix, suffix: prefix + suffix)
@wkf.provide('{prefix}.echo.{suffix}')
def echo(prefix, suffix=""):
    return prefix + suffix


def test_run_mutate():
    res = wkf.run('ham.echo')
    assert res == 'HAM'
    res = wkf.run('ham.echo.spam')
    assert res == 'HAMHAMspam'
