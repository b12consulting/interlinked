import pytest

from interlinked import Workflow
from interlinked.exceptions import InvalidValue


# Simple test, we simply match an entry, config content is static
cfg = {
    "hello.{world:identifier}": {
        "param": " from conf",
    },
    "hello.ham": {"param": " FROM CONF"},
}
wkf = Workflow("My workflow", config=cfg, base_kw={"world": "from wkf"})


@wkf.provide("hello")
@wkf.provide("hello.{world}")
def echo(world, param="", fmt_param=""):
    return world + param


def test_param_from_conf():
    res = wkf.run("hello.spam")
    assert res == "spam from conf"

    res = wkf.run("hello.ham")
    assert res == "ham FROM CONF"

    res = wkf.run("hello")
    assert res == "from wkf"



# Tests config with parameterized content
cfg2 = {
    "hello.{world:identifier}": {
        "fmt_param": "from conf ({world})",
    },
}
wkf2 = Workflow("My fmt workflow", config=cfg2)


@wkf2.provide("hello.{world}")
def fmt_echo(fmt_param):
    return fmt_param


def test_fmt_param_from_conf():
    res = wkf2.run("hello.spam")
    assert res == "from conf (spam)"


# Tests config with parameterized content and valid format specifier
cfg3 = {
    "hello.{world:identifier}": {
        "fmt_param": "from conf ({world:identifier})",
    },
}
wkf3 = Workflow("My fmt-spec workflow", config=cfg3)


@wkf3.provide("hello.{world}")
def fmt_spec_echo(fmt_param):
    return fmt_param


def test_fmt_spec_param_from_conf():
    res = wkf3.run("hello.spam")
    assert res == "from conf (spam)"


# Tests config with parameterized content and an invalid valid format specifier
cfg4 = {
    "hello.{world:identifier}": {
        "fmt_param": "from conf ({world:uuid})",
    },
}
wkf4 = Workflow("My fmt-invalid-spec workflow", config=cfg4)


@wkf4.provide("hello.{world}")
def fmt_invalid_spec_echo(fmt_param):
    return fmt_param


def test_fmt_invalid_spec_param_from_conf():
    with pytest.raises(InvalidValue):
        wkf4.run("hello.spam")
