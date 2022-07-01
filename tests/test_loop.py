import pytest

from interlinked import Workflow
from interlinked.exceptions import LoopException, UnknownDependency


base = Workflow("base")

@base.provide('first')
def first(value):
    return value + other

@base.depend(value='first')
@base.provide('second')
def second(value):
    return value


loopy = Workflow("loopy")

@loopy.depend(value='third', other="zero")
@loopy.provide('first')
def first(value, other):
    return value + other

@loopy.depend(value='first')
@loopy.provide('second')
def second(value):
    return value

@loopy.depend(value='second')
@loopy.provide('third')
def third(value):
    return value



def test_loop():
    # Base workflow should be fine
    base.validate()

    # Zero does not exists yet
    with pytest.raises(UnknownDependency):
        loopy.validate()

    @loopy.provide('zero')
    def zero():
        return

    with pytest.raises(LoopException):
        loopy.validate()
