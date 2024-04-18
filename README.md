
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

from interlinked.workflow import default_workflow as wkf

wkf.resolve = lambda target, **kw: wkf.run(target, **kw).upper()
print(wkf.run("many_echo"))  # -> TEST TEST
```

As you can see, we rebind the `resolve` method of the workflow.

The workflow object is instanciated for us when interlinked is
imported. This object is responsible to keep track of dependencies
(based on `depend` decorator) and to run our code (based on `provide`
decorator).

Resolve is the method that is invoked by the workflow to reify the
parameters defined in `depend`, by default it simply runs the
corresponding function and reuse the returned values as input.

By rebinding the `resolve` method we can inject custom logic at each
step of the workflow.


# Advanced usages

## Load parameters from config file

You can provide a config dict to a workflow (or declare add it to the
default workflow with `set_config`):

``` python
cfg = {
    "hello.{world}" : {
        "param" : " from conf",
    },
    "hello.ham" : {
        "param" : " FROM CONF"
    }
}
wkf = Workflow(config=cfg)
```

It will be implicitly used when a "provide" route is matched:

``` python
@wkf.provide("hello")
@wkf.provide("hello.{world}")
def echo(world, param=""):
    return f"hello {world} {param}"


res = wkf.run("hello.spam")
assert res  == "hello spam from conf"

res = wkf.run("hello.ham")
assert res == "hello ham FROM CONF"
```


## Multi workflow

Above examples use the default workflow object. We can use explicit ones like this

``` python
wkf_a = Workflow("wkf-a")
wkf_b = Workflow("wkf-b")

@wkf_a.provide('echo-one')
def echo_one():
    return 'one A'

@wkf_b.provide('echo-one')
def echo_one():
    return 'one B'

assert wkf_b.run('echo-one') == 'one B'
```
