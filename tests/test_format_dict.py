from interlinked.workflow import rformat, set_config, provide, run


def test_fmt_dict():
    # on key
    d = {"ham-{spam}": "one"}
    assert rformat(d, spam="SPAM") == {"ham-SPAM": "one"}
    # on value
    d = {"ham-spam": "foo-{bar}"}
    assert rformat(d, bar="BAR") == {"ham-spam": "foo-BAR"}


def test_fmt_list():
    d = ["ham-{spam}", "one"]
    assert rformat(d, spam="SPAM") == ["ham-SPAM", "one"]


def test_fmt_str():
    d = "foo-{bar}"
    assert rformat(d, bar="BAR") == "foo-BAR"


def test_fmt_combined():
    d = {"ham-{spam}": ["foo-{bar}", {"ham": "{spam}"}]}
    res = rformat(d, spam="SPAM", bar="BAR")
    assert res == {"ham-SPAM": ["foo-BAR", {"ham": "SPAM"}]}


@provide("echo.{name}")
def echo(url):
    return url


def test_fmt_with_wkf():
    set_config({"echo.{name}": {"url": "http://host/{name}.json"}})

    assert run("echo.spam") == "http://host/spam.json"
