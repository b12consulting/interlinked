import pytest
from interlinked import depend, provide, default_workflow
from interlinked.exceptions import LoopException


# Create a graph that looks like
# A
# - B
#   - D
# - C
#   - D
#   - B

@provide("a")
def fn_a():
    return "a"


@depend(a="a", c="c")
@provide("b")
def fn_b(a, c):
    return a + "b" + c


@depend(a="a")
@provide("c")
def fn_c(a):
    return a + "c"

@depend(b="b", c="c")
@provide("d")
def fn_d(b, c):
    return b + c


def test_diamond():
    default_workflow.validate()


def test_direct_loop():
    wkf = default_workflow.clone(name="test-1")
    # Add new link C -> D
    wkf.depend(d="d")(fn_c)

    with pytest.raises(LoopException):
        wkf.validate()


def test_indirect_loop():
    wkf = default_workflow.clone(name="test-2")
    # Add new links D -> E -> A
    wkf.depend(d="d")
    wkf.provide("e")
    def fn_e(d):
        pass

    wkf.depend(e="e")(fn_a)

    with pytest.raises(LoopException):
        wkf.validate()



