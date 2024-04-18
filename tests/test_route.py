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
