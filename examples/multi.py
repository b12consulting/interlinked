from interlinked import Workflow

wkf_a = Workflow("wkf-a")
wkf_b = Workflow("wkf-b")

@wkf_a.provide('echo-one')
def echo_one():
    return 'one A'

@wkf_b.provide('echo-one')
def echo_one():
    return 'one B'

assert wkf_b.run('echo-one') == 'one B'
