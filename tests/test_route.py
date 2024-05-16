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

    fn, kw = router.match("a")
    assert fn(**kw) == "a"

    fn, kw = router.match("one.b")
    assert fn(**kw) == "b"

    fn, kw = router.match("one.b.c")
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
    fn, kw = router.match("one/10")
    assert fn(**kw) == "10"  # -> still a string, no cast implemented yet

    # 'ten' does not match an int
    assert None == router.match("one/ten")

    # Match simple string
    fn, kw = router.match("two/two")
    assert fn(**kw) == "two"

    # Match path
    fn, kw = router.match("/three/some/path/file.txt")
    assert ["some/path", "file", "txt"]

    # Match an uuid
    uuids = [
        "40B4550B-F1DD-4846-BC70-D8F5F235E72B",
        "40b4550b-f1dd-4846-bc70-d8f5f235e72b",
    ]
    for uuid in uuids:
        fn, kw = router.match("four/" + uuid)
        assert fn(**kw) == uuid

    # with ambiguity on _
    fn, kw = router.match("five_one_two_three")
    assert fn(**kw) == ("one_two", "three")

    # with ambiguity on - (but we specify uuid param)
    fn, kw = router.match("six_one-40b4550b-f1dd-4846-bc70-d8f5f235e72b")
    assert fn(**kw) == ("one", "40b4550b-f1dd-4846-bc70-d8f5f235e72b")
