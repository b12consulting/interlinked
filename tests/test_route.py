from interlinked.router import Router


def test_add_simple_route():
    routes = {
        "one": 1,
        "one.two": 2,
        "one.two.three": 3,
    }

    router = Router()
    for key, value in routes.items():
        router.add(key, value)

    # ok routes
    for key, value in routes.items():
        assert router.match(key).value == value

    # not ok routes
    for route in ("spam", "one.spam.three"):
        assert not router.match(route)


def test_add_parameterized_route():
    router = Router()
    router.add_routes(
        {
            "{one:identifier}": lambda one: one,
            "one.{two:identifier}": lambda two: two,
            "one.{two:identifier}.{three:identifier}": lambda two, three: (two, three),
        }
    )

    match = router.match("a")
    fn, kw = match.value, match.kw
    assert fn(**kw) == "a"

    match = router.match("one.b")
    fn, kw = match.value, match.kw
    assert fn(**kw) == "b"

    match = router.match("one.b.c")
    fn, kw = match.value, match.kw
    assert fn(**kw) == ("b", "c")

    # not ok routes
    for route in ("spam.b.c", "one.b.c.d"):
        assert not router.match(route)


def test_param_type():
    router = Router()
    router.add_routes(
        {
            "one/{one:int}": lambda one: one,
            "two/{two:str}": lambda two: two,
            "/three/{parents:path}/{name}.{ext}": lambda parents, name, ext: [
                parents,
                name,
                ext,
            ],
            "four/{four:uuid}": lambda four: four,
            "five_{ham}_{spam}": lambda ham, spam: (ham, spam),
            "six_{ham}-{spam:uuid}": lambda ham, spam: (ham, spam),
        }
    )

    # "one/" match an int
    match = router.match("one/10")
    fn, kw = match.value, match.kw
    assert fn(**kw) == "10"  # -> still a string, no cast implemented yet

    # 'ten' does not match an int
    assert None == router.match("one/ten")

    # Match simple string
    match = router.match("two/two")
    fn, kw = match.value, match.kw
    assert fn(**kw) == "two"

    # Match path
    match = router.match("/three/some/path/file.txt")
    fn, kw = match.value, match.kw
    assert ["some/path", "file", "txt"]

    # Match an uuid
    uuids = [
        "40B4550B-F1DD-4846-BC70-D8F5F235E72B",
        "40b4550b-f1dd-4846-bc70-d8f5f235e72b",
    ]
    for uuid in uuids:
        match = router.match("four/" + uuid)
        fn, kw = match.value, match.kw
        assert fn(**kw) == uuid

    # with ambiguity on _
    match = router.match("five_one_two_three")
    fn, kw = match.value, match.kw
    assert fn(**kw) == ("one_two", "three")

    # with ambiguity on - (but we specify uuid param)
    match = router.match("six_one-40b4550b-f1dd-4846-bc70-d8f5f235e72b")
    fn, kw = match.value, match.kw
    assert fn(**kw) == ("one", "40b4550b-f1dd-4846-bc70-d8f5f235e72b")
