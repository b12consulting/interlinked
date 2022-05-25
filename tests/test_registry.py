import pytest
from interlinked.registry import run, Registry, provide, depend


@provide('echo')
@provide('echo.{name}')
def echo(name='default'):
    return name


@depend(value='echo.test')
@provide('many_echo')
def many_echo(value, repeat=2):
    return ' '.join([value] * repeat)


def test_run_no_depends():
    res = run('echo')
    assert res == 'default'

    res = run('echo.test')
    assert res == 'test'

    # Works also with the pattern itself, and explicit parameter
    registry = Registry(name="explicit")
    res = registry.run('echo.{name}')
    assert res == 'explicit'

    # We get None if the name is not matched
    with pytest.raises(KeyError):
        registry.by_name('spam')


def test_run_with_depends():
    registry = Registry()

    res = registry.run('many_echo')
    assert res == 'test test'

    registry_bis = Registry(repeat=3, name="test")
    registry_bis.resolve = lambda name: registry_bis.run(name)
    res = registry_bis.run('many_echo')
    assert res == 'test test test'

def test_run_custom_resolver():
    pass  # TODO
