from interlinked import Workflow

wkf_a = Workflow("wkf-a")
wkf_b = Workflow("wkf-b")

@wkf_a.provide('echo-one')
def echo_one():
    return 'one A'

@wkf_b.provide('echo-one')
def echo_one():
    return 'one B'


if __name__ == "__main__":
    assert wkf_b.run('echo-one') == 'one B'
