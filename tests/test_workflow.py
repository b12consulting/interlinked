from collections import defaultdict

import pytest
from interlinked import Workflow

LOGS = defaultdict(int)
wkf = Workflow("test-wkf")


@wkf.provide('echo')
@wkf.provide('echo.{name}')
def echo(name='default'):
    return name


@wkf.depend(value='echo.test')
@wkf.provide('many_echo')
def many_echo(value, repeat=2):
    return ' '.join([value] * repeat)


@wkf.provide('logged.{name}')
def logged(name):
    LOGS[name] += 1
    return name

@wkf.depend(first='logged.{name}', second='logged.{name}')
@wkf.provide('logged-repeater.{name}')
def logged_repeater(first, second):
    return first + second


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


def test_run_cache():
    # Distinct runs
    wkf.run('logged.ham')
    wkf.run('logged.ham')
    wkf.run('logged.spam')
    assert LOGS == {'ham': 2, 'spam': 1}

    # Commnon run
    assert wkf.run('logged-repeater.foo') == "foofoo"
    assert LOGS == {'ham': 2, 'spam': 1, 'foo': 1}
