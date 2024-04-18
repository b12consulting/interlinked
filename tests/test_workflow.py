import pytest
from interlinked import Workflow


wkf = Workflow("test-wkf")

@wkf.provide('echo')
@wkf.provide('echo.{name}')
def echo(name='default'):
    return name


@wkf.depend(value='echo.test')
@wkf.provide('many_echo')
def many_echo(value, repeat=2):
    return ' '.join([value] * repeat)


def test_run_no_depends():
    res = wkf.run('echo')
    assert res == 'default'

    res = wkf.run('echo.test')
    assert res == 'test'

    # Works also with the pattern itself, and explicit parameter
    res = wkf.run('echo.{name}', name="explicit")
    assert res == 'explicit'

    # We get None if the name is not matched
    with pytest.raises(KeyError):
        wkf.by_name('spam')


def test_run_with_depends():
    res = wkf.run('many_echo')
    assert res == 'test test'

    workflow_bis = wkf.kw(repeat=3, name="test")
    res = workflow_bis.run('many_echo')
    assert res == 'test test test'


def test_run_custom_resolver():
    wkf.resolve = lambda name: wkf.run(name)
    resolver = lambda name: wkf.run(name).upper()
    wkf.resolve = resolver
    res = wkf.run('many_echo')
    assert res == 'TEST TEST'
