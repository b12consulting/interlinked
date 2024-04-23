from interlinked.router import Router


def test_add_simple_route():
    routes = {
        'one': 1,
        'one.two': 2,
        'one.two.three': 3,
    }

    router = Router()
    for key, value in routes.items():
        router.add(key, value)

    # ok routes
    for key, value in routes.items():
        assert router.match(key).value == value

    # not ok routes
    for route in ('spam', 'one.spam.three'):
        assert not router.match(route)


def test_add_parameterized_route():
    router = Router()
    router.add_routes({
        '{one}': lambda one: one,
        'one.{two}': lambda two: two,
        'one.{two}.{three}': lambda two, three: (two, three),
    })

    fn, kw = router.match('a')
    assert fn(**kw) == 'a'

    fn, kw = router.match('one.b')
    assert fn(**kw) == 'b'

    fn, kw = router.match('one.b.c')
    assert fn(**kw) == ('b', 'c')

    # not ok routes
    for route in ('spam.b.c', 'one.b.c.d'):
        assert not router.match(route)


def test_param_type():
    router = Router()
    router.add_routes({
        'one/{one:int}': lambda one: one,
        'two/{two:str}': lambda two: two,
        '/root/{parents:path}/{name}.{ext}':
          lambda parents, name, ext: [parents, name, ext],
    })

    # "one/" match an int
    fn, kw = router.match('one/10')
    assert fn(**kw) == "10"  # -> still a string, no cast implemented yet

    # 'ten' does not match an int
    assert None == router.match('one/ten')

    # Base case: a simple string
    fn, kw = router.match('two/two')
    assert fn(**kw) == "two"

    # Base case: a path
    fn, kw = router.match('/root/some/path/file.txt')
    assert ["some/path", "file", "txt"]
