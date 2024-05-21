from interlinked import Workflow


cfg = {
    "hello.{world:identifier}": {
        "param": " from conf",
    },
    "hello.ham": {"param": " FROM CONF"},
}

wkf = Workflow("My workflow", config=cfg, base_kw={"world": "from wkf"})


@wkf.provide("hello")
@wkf.provide("hello.{world}")
def echo(world, param=""):
    return world + param


def test_param_from_conf():

    res = wkf.run("hello.spam")
    assert res == "spam from conf"

    res = wkf.run("hello.ham")
    assert res == "ham FROM CONF"

    res = wkf.run("hello")
    assert res == "from wkf"
