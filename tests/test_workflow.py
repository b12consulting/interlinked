import pytest
from interlinked.workflow import run, default_workflow, provide, depend


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
    res = run('echo.{name}', name="explicit")
    assert res == 'explicit'

    # We get None if the name is not matched
    with pytest.raises(KeyError):
        default_workflow.by_name('spam')


def test_run_with_depends():
    res = run('many_echo')
    assert res == 'test test'

    workflow_bis = default_workflow.clone(repeat=3, name="test")
    workflow_bis.resolve = lambda name: workflow_bis.run(name)
    res = workflow_bis.run('many_echo')
    assert res == 'test test test'


def test_run_custom_resolver():
    pass  # TODO
