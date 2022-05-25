from collections import defaultdict
from functools import partial
from inspect import signature, Signature

from interlinked import Router


class Item:

    def __init__(self, kw=None):
        self.fn = None
        self.kw = kw or {}
        self.dependencies = {}

    def __call__(self, fn):
        Registry.by_fn[fn].append(self)
        self.fn = fn
        return fn

    def depend(self, **dependencies):
        self.dependencies.update(dependencies)
        return self


class Registry:
    router = Router()
    by_fn = defaultdict(list)

    def __init__(self, **base_kw):
        self.base_kw = base_kw
        self.resolve = self.run

    @classmethod
    def provide(cls, pattern, **kw):
        if pattern in Registry.router:
            raise ValueError(f"{pattern} already defined in Registry")
        item = Item(kw)
        Registry.router.add(pattern, item)
        return item

    @classmethod
    def depend(cls, **dependencies):
        def decorator(fn):
            for item in Registry.by_fn[fn]:
                item.dependencies = {**dependencies, **item.dependencies}
            return fn
        return decorator

    @classmethod
    def by_name(cls, name):
        '''
        Find a function that match the given name. Either because the
        exact name is found. Either through pattern matching. Returns
        a tuple containing the function, the parameters extracted by
        pattern matching and the dependencies needed by this function.
        '''
        match = cls.router.match(name)
        if not match:
            raise KeyError(f"No ressource found in registry for '{name}'")
        # match contains an extra dict of kw, that contains values
        # used for pattern matching
        item, match_kw = match
        return item.fn, {**item.kw,  **match_kw}, item.dependencies

    def run(self, resource_name, **extra_kw):
        # print(resource_name, extra_kw)
        fn, match_kw, dependencies = Registry.by_name(resource_name)
        kw = {**self.base_kw, **match_kw, **extra_kw}
        # Resolve dependencies
        if dependencies:
            if not self.resolve:
                raise RuntimeError("Missing resolve function on registry")

            for alias, table in dependencies.items():
                table = table.format(**kw)
                read = bind(self.resolve, [table], kw.copy())
                kw[alias] = read()

        # Run function
        return bind(fn, kw=kw)()


# Define shortcuts
default_registry = Registry()
run = default_registry.run
provide = Registry.provide # XXX use default_registry ?
depend = Registry.depend



def bind(fn, args=None, kw=None):
    '''
    Bind keyword parameters to the given function (if needed).
    '''

    args = args or []
    kw = kw or {}

    # Inspect function parameters
    params = signature(fn).parameters
    has_var_kw = any(p.kind == p.VAR_KEYWORD for p in params.values())
    positionals = {}
    for pos, p in enumerate(params.values()):
        if p.default is Signature.empty:
            positionals[p.name] = pos
    in_pos = lambda n: n in positionals and positionals[n] < len(args)

    # Filter out uneeded parameters
    partial_kw = {}
    for name, value in kw.items():
        if name not in params and not has_var_kw:
            # Skip unsupported params
            continue
        if in_pos(name):
            # This param is already defined in args
            continue
        partial_kw[name] = value

    if not (args or partial_kw):
        return fn
    # if has_var_kw:
    #     # Inject unprocessed params
    #     extra_kw = {k:v for k, v in kw.items() if k not in partial_kw}
    # else:
    #     extra_kw = {}

    return partial(fn, *args, **partial_kw)
