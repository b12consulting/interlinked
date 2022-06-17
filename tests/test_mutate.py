#
from interlinked.workflow import run, provide, mutate


@mutate(prefix=lambda prefix: prefix.upper())
@provide('{prefix}.echo')
@mutate(suffix=lambda prefix, suffix: prefix + suffix)
@provide('{prefix}.echo.{suffix}')
def echo(prefix, suffix=""):
    return prefix + suffix

def test_run_mutate():
    res = run('ham.echo')
    assert res == 'HAM'
    res = run('ham.echo.spam')
    assert res == 'HAMHAMspam'
