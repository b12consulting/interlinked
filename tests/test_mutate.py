#
from interlinked import Workflow

wkf = Workflow("test-mutate")


@wkf.mutate(prefix=lambda prefix: prefix.upper())
@wkf.provide("{prefix}.echo")
@wkf.mutate(suffix=lambda prefix, suffix: prefix + suffix)
@wkf.provide("{prefix}.echo.{suffix}")
def echo(prefix, suffix=""):
    return prefix + suffix


def test_run_mutate():
    res = wkf.run("ham.echo")
    assert res == "HAM"
    res = wkf.run("ham.echo.spam")
    assert res == "HAMHAMspam"



@wkf.provide("get-extra.{name}")
def get_extra(name):
    return name

# Not mutate
@wkf.depend(extra="get-extra.static")
@wkf.provide("static.echo-extra")
# With mutate
@wkf.depend(extra="get-extra.{prefix}")
@wkf.mutate(extra=lambda prefix: {"my_key": prefix})
@wkf.provide("{prefix}.echo-extra")
def echo_extra(extra=None):
    return extra


def test_run_mutate_extra():
    res = wkf.run("ham.echo-extra")
    assert res == {"my_key": "ham"}

    res = wkf.run("static.echo-extra")
    assert res == "static"
