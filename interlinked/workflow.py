from collections import defaultdict
from functools import partial
from inspect import signature, Signature

from interlinked import Router


class Item:

    def __init__(self, workflow, kw=None):
        self.workflow = workflow
        self.fn = None
        self.kw = kw or {}
        self.dependencies = {}
        self.mutators = {}

    def __call__(self, fn):
        self.workflow.by_fn[fn].append(self)
        self.fn = fn
        return fn

    def depend(self, **dependencies):
        self.dependencies.update(dependencies)
        return self


class Workflow:

    def __init__(self, router=None, by_fn=None, base_kw=None, resolve=None):
        self.router = router or Router()
        self.by_fn = defaultdict(list)
        self.by_fn.update(by_fn or {})
        self.base_kw = {}
        self.base_kw.update(base_kw or {})
        self.resolve = resolve or self.run

    @classmethod
    def new(cls, **base_kw):
        return Workflow(
            base_kw=base_kw
        )

    def clone(self, **kw):
        new_wkf = Workflow(
            router=self.router.clone(),
            by_fn=self.by_fn,
            base_kw={**self.base_kw, **kw},
        )
        return new_wkf

    def provide(self, pattern, **kw):
        if pattern in self.router:
            raise ValueError(f"{pattern} already defined in Workflow")
        item = Item(self, kw)
        self.router.add(pattern, item)
        return item

    def depend(self, **dependencies):
        def decorator(fn):
            for item in self.by_fn[fn]:
                item.dependencies = {**dependencies, **item.dependencies}
            return fn
        return decorator

    def mutate(self, **mutators):
        def decorator(fn):
            for item in self.by_fn[fn]:
                item.mutators = {**mutators, **item.mutators}
            return fn
        return decorator

    def by_name(self, name):
        '''
        Find a function that match the given name. Either because the
        exact name is found. Either through pattern matching. Returns
        a tuple containing the function, the parameters extracted by
        pattern matching and the dependencies needed by this function.
        '''
        match = self.router.match(name)
        if not match:
            raise KeyError(f"No ressource found in workflow for '{name}'")
        # match contains an extra dict of kw, that contains values
        # used for pattern matching
        item, match_kw = match
        return item, {**item.kw,  **match_kw}

    def run(self, resource_name, **extra_kw):
        item, match_kw = self.by_name(resource_name)
        kw = {**self.base_kw, **match_kw, **extra_kw}
        # Resolve dependencies
        if item.dependencies:
            if not self.resolve:
                raise RuntimeError("Missing resolve function on workflow")

            for alias, table in item.dependencies.items():
                table = table.format(**kw)
                read = bind(self.resolve, [table], kw.copy())
                kw[alias] = read()

        # Mutate parameters
        for alias, fn in item.mutators.items():
            kw[alias] = bind(fn, kw=kw)()

        # Run function
        return bind(item.fn, kw=kw)()


# Define shortcuts
default_workflow = Workflow()
run = default_workflow.run
provide = default_workflow.provide
depend = default_workflow.depend
mutate = default_workflow.mutate



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
