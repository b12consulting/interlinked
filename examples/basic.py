from interlinked import run, provide, depend


@provide('echo')
@provide('echo.{name}', 'echo-bis.{name}')
def echo(name='default'):
    return name, name + "-bis"


@depend(value='echo.test', value_bis="echo-bis.test")
@provide('many_echo')
def many_echo(value, value_bis, repeat=2):
    return ' '.join([value] * repeat)

result = run("echo.spam")
print(result)  # -> spam

result = run("many_echo", repeat=4)
print(result)  # -> test test test test


from interlinked.workflow import default_workflow as wkf

wkf.resolve = lambda target, **kw: wkf.run(target, **kw).upper()
print(wkf.run("many_echo"))
