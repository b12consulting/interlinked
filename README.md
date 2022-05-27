
# Quickstart

This initial example shows first pattern matching and then dependency
resolution.

```python
from interlinked import run, provide, depend

@provide('echo')
@provide('echo.{name}')
def echo(name='default'):
    return name


@depend(value='echo.test')
@provide('many_echo')
def many_echo(value, repeat=2):
    return ' '.join([value] * repeat)

result = run("echo.spam")
print(result)  # -> spam

result = run("many_echo", repeat=4)
print(result)  # -> test test test test

```


This second example shows custom dependency resolution (based on
previous code).


```python
from interlinked.workflow import Workflow

workflow = Workflow()
workflow.resolve = lambda target, **kw: workflow.run(target, **kw).upper()
print(workflow.run("many_echo"))  # -> TEST TEST
```


# Recipes

TODO ...
