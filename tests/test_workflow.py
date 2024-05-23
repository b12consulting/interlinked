from collections import defaultdict

import pytest
from interlinked import Workflow

LOGS = defaultdict(int)
wkf = Workflow("test-wkf")


@wkf.provide("echo")
@wkf.provide("echo.{name}")
def echo(name="default"):
    return name


@wkf.depend(value="echo.test")
@wkf.provide("many_echo")
def many_echo(value, repeat=2):
    return " ".join([value] * repeat)


def test_run_no_depends():
    res = wkf.run("echo")
    assert res == "default"

    res = wkf.run("echo.test")
    assert res == "test"

    # Works also with the pattern itself, and explicit parameter
    res = wkf.run("echo.{name}", name="explicit")
    assert res == "explicit"

    # We get None if the name is not matched
    with pytest.raises(KeyError):
        wkf.by_name("spam")


def test_run_with_depends():
    res = wkf.run("many_echo")
    assert res == "test test"

    workflow_bis = wkf.kw(repeat=3, name="test")
    res = workflow_bis.run("many_echo")
    assert res == "test test test"


@wkf.provide("logged.{name}")
def logged(name):
    LOGS[name] += 1
    return name


@wkf.depend(first="logged.{name}", second="logged.{name}")
@wkf.provide("logged-repeater.{name}")
def logged_repeater(first, second):
    return first + second


def test_run_cache():
    # Distinct runs
    wkf.run("logged.ham")
    wkf.run("logged.ham")
    wkf.run("logged.spam")
    assert LOGS == {"ham": 2, "spam": 1}

    # Commnon run
    assert wkf.run("logged-repeater.foo") == "foofoo"
    assert LOGS == {"ham": 2, "spam": 1, "foo": 1}
    LOGS.clear()


@wkf.provide("upper.{name}", "lower.{name}")
def multi(name):
    LOGS["multi"] += 1
    return name.upper(), name.lower()


@wkf.depend(upper="upper.{name}", lower="lower.{name}")
@wkf.provide("upper-and-lower.{name}")
def up_and_low(upper, lower):
    return upper + lower


def test_multi_provide():
    # Distinct runs
    assert wkf.run("upper-and-lower.spam") == "SPAMspam"
    assert LOGS["multi"] == 1
    assert wkf.run("upper-and-lower.FOO") == "FOOfoo"
    assert LOGS["multi"] == 2
    LOGS.clear()


def test_run_match_type():
    wkf = Workflow("test_run_match_type")

    @wkf.provide("my-uuid.{name:uuid}", "my-id.{name:identifier}", "my-int.{name:int}")
    def my_uuid(name="default"):
        return name, name, name

    res = wkf.run("my-uuid.40b4550b-f1dd-4846-bc70-d8f5f235e72b")
    assert res == "40b4550b-f1dd-4846-bc70-d8f5f235e72b"

    res = wkf.run("my-int.123")
    assert res == "123"
    res = wkf.run("my-id.abc")
    assert res == "abc"
