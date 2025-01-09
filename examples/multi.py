from interlinked import Workflow

wkf_a = Workflow("wkf-a")
wkf_b = Workflow("wkf-b")
wkf_c = Workflow("wkf-c")
wkf_d = Workflow("wkf-d")


# Independant workflows
@wkf_a.provide('echo-a')
def echo_a():
    return 'A'


@wkf_b.provide('echo-b')
def echo_b():
    return 'B'


# Mixed workflows
@wkf_c.provide('echo-c')
def echo_c():
    return 'C'


@wkf_c.depend(parent='echo-c')
@wkf_d.provide('echo-d')
def echo_d(parent):
    return 'D' + parent


if __name__ == "__main__":
    assert wkf_d.run('echo-d') == 'DC'
