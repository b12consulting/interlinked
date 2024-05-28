import re
from dataclasses import dataclass
from typing import Any, Callable, Optional
from collections import defaultdict
from functools import partial
from inspect import signature, Signature
from itertools import chain
from string import Formatter
import time
import logging

from interlinked.router import Router, Match, VALUE_PATTERNS
from interlinked.exceptions import NoRootException, LoopException, UnknownDependency, InvalidValue

logger = logging.getLogger("interlinked")


class Cell:
    """
    A cell is a node in the workflow it associate one or more
    pattern to a function and keep track of its dependencies.
    """

    def __init__(
        self, workflow: "Workflow", patterns: tuple[str, ...], kw: Optional[dict] = None
    ):
        self.patterns = [Pattern.from_string(p) for p in patterns]
        self.workflow = workflow
        self.fn = None
        self.kw = kw or {}
        self.dependencies = {}
        self.mutators = {}

    def __call__(self, fn: Callable):
        self.workflow.by_fn[fn].append(self)
        self.fn = fn
        return fn

    def depend(self, dependencies):
        self.dependencies = {**dependencies, **self.dependencies}
        return self


class Workflow:

    _registry = {}

    def __init__(
        self,
        name: str,
        router: Optional[Router] = None,
        by_fn: Optional[dict[Callable, list[Cell]]] = None,
        base_kw: Optional[dict] = None,
        config: Optional[dict] = None,
    ):
        if name:
            if name in Workflow._registry:
                raise ValueError(f"Workflow {name} already defined!")
            Workflow._registry[name] = self
        self.name = name
        self.router = router or Router()
        self.by_fn = defaultdict(list)
        self.by_fn.update(by_fn or {})
        self.base_kw = {}
        self.base_kw.update(base_kw or {})
        self._validated = False
        self.config_router = Router()
        if config:
            self.set_config(config)

    @classmethod
    def get(cls, name: str) -> "Workflow | None":
        return cls._registry.get(name)

    def set_config(self, config: dict):
        self.config_router = Router(**config)

    def validate(self):
        if self._validated:
            return

        deps = self.deps()
        roots = set(deps) - set(chain.from_iterable(deps.values()))
        if not roots:
            raise NoRootException(f"No roots for workflow '{self.name}'")

        for root in roots:
            self._validate(root, deps, ancestors=tuple())
        self._validated = True

    def _validate(self, parent, deps, ancestors):
        children = deps[parent]
        for child in children:
            if child in ancestors:
                msg = (
                    f'Loop detected in workflow "{self.name}" '
                    f'(validation failed when evaluating "{child}")'
                )
                raise LoopException(msg)
            self._validate(child, deps, ancestors + (child,))


    def deps(self):
        """
        build {parent: [child]} dependency dictionary.
        """
        # Init dict
        p2c = {p: [] for p in self.router.routes}
        for pattern in self.router.routes:
            match = self.router.match(pattern)
            cell = match.value
            parents = (p.pattern for p in cell.dependencies.values())
            for parent in parents:
                if parent not in p2c:
                    # Try pattern matching
                    match = self.router.match(parent)
                    if match:
                        parent = match.route
                    else:
                        raise UnknownDependency(
                            f"Dependency '{parent}' is not known "
                            f"in workflow '{self.name}'"
                        )
                p2c[parent].append(pattern)

        return p2c

    def clone(
        self,
        name: Optional[str] = None,
        config: Optional[dict] = None,
        kw: Optional[dict] = None,
    ):
        kw = kw or {}
        config = config or self.config_router.routes.copy()
        new_wkf = Workflow(
            name=name or self.name + "_clone",
            router=self.router.clone(),
            by_fn=self.by_fn,
            base_kw={**self.base_kw, **kw},
            config=config,
        )
        return new_wkf

    def kw(self, **kw):
        return self.clone(kw=kw)

    def config(self, config: dict):
        return self.clone(config=config)

    def provide(self, *patterns: str, **kw):
        self._validated = False
        for pattern in patterns:
            if pattern in self.router:
                msg = f"{pattern} already defined in Workflow '{self.name}'"
                raise ValueError(msg)
        cell = Cell(self, patterns, kw)
        for pattern in patterns:
            self.router.add(pattern, cell)
        return cell

    def depend(self, **dependencies):
        self._validated = False
        if dependencies:
            # convert pattern strings into objects
            dependencies = {k: Pattern.from_string(v) for k, v in dependencies.items()}

        def decorator(fn):
            for cell in self.by_fn[fn]:
                cell.depend(dependencies)
            return fn

        return decorator

    def mutate(self, **mutators):
        def decorator(fn):
            for cell in self.by_fn[fn]:
                cell.mutators = {**mutators, **cell.mutators}
            return fn

        return decorator

    def by_name(self, name: str) -> Match:
        """
        Find a function that match the given name. Either because the
        exact name is found. Either through pattern matching. Returns
        a tuple containing the function, the parameters extracted by
        pattern matching and the dependencies needed by this function.
        """
        match = self.router.match(name)
        if not match:
            raise KeyError(f"No resource found in workflow for '{name}'")
        # match contains an extra dict of kw, that contains values
        # used for pattern matching
        return match

    def run(self, *resource_name: str, **extra_kw):
        """
        Create a Run instance and execute it
        """
        run = Run(self, **extra_kw)
        results = tuple(run.resolve(name) for name in resource_name)
        if len(results) == 1:
            return results[0]
        return results


class Run:
    def __init__(self, wkf, **extra_kw):
        self.wkf = wkf
        self.extra_kw = extra_kw
        # Cache at instance level
        self.cache = {}

    def resolve(self, resource_name) -> Any:
        if (res := self.cache.get(resource_name)) is not None:
            return res

        # Search fn
        match = self.wkf.by_name(resource_name)
        # Identify config cell and apply auto-formating
        config_entry = self.wkf.config_router.get(resource_name, {})
        if config_entry:
            config_entry = rformat(config_entry, **match.kw)

        kw = {**self.wkf.base_kw, **match.kw, **self.extra_kw, **config_entry}
        # Resolve dependencies
        cell = match.value
        if cell.dependencies:
            for alias, resource in cell.dependencies.items():
                try:
                    resource = resource.fmt(kw)
                except KeyError as e:
                    raise KeyError(
                        f"Missing dependency {resource} for {resource_name} in workflow {self.wkf.name}"
                    ) from e
                read = bind(self.resolve, [resource])
                kw[alias] = read()

        # Mutate parameters
        for alias, fn in cell.mutators.items():
            kw[alias] = bind(fn, kw=kw)()

        # Run function
        logger.debug(f"Workflow {self.wkf.name} running {cell.fn.__name__}")

        start_time = time.time()
        res = bind(cell.fn, kw=kw)()
        end_time = time.time()

        execution_time = end_time - start_time
        logger.debug(f"Call of {cell.fn.__name__} took {execution_time:.3f}s")

        # Cache & return simple cell
        if len(cell.patterns) == 1:
            self.cache[resource_name] = res
            return res

        # If a cell contains multiple patterns (multi-provide
        # decorator), extract the relevant one
        assert isinstance(res, tuple)
        for pattern, pattern_res in zip(cell.patterns, res):
            self.cache[pattern.fmt(match.kw)] = pattern_res
        raw_patterns = [p.pattern for p in cell.patterns]
        return res[raw_patterns.index(match.route)]


# Define shortcuts
default_workflow = Workflow("default_workflow")
run = default_workflow.run
provide = default_workflow.provide
depend = default_workflow.depend
mutate = default_workflow.mutate
set_config = default_workflow.set_config


def bind(fn: Callable, args=None, kw=None):
    """
    Bind keyword parameters to the given function (if needed).
    """

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

        # Add value to partial_kw
        partial_kw[name] = value

    if not (args or partial_kw):
        return fn

    return partial(fn, *args, **partial_kw)


def rformat(cfg: list | dict | str, **kw):
    """
    Recursively format content of cfg with kw (in-place!)
    """
    # Dict: handle keys and values
    if isinstance(cfg, dict):
        for key in list(cfg):
            if (fmt_key := rformat(key, **kw)) != key:
                cfg[fmt_key] = cfg.pop(key)

        for key, value in cfg.items():
            cfg[key] = rformat(value, **kw)
    # List
    if isinstance(cfg, list):
        cfg = [rformat(cell, **kw) for cell in cfg]

    # Simple string
    if isinstance(cfg, str):
        ptrn = Pattern.from_string(cfg)
        cfg = ptrn.fmt(kw)

    return cfg


@dataclass
class PatternField:
    literal_text: str
    field_name: Optional[str]
    specifier: Optional[str]

    def fmt(self, kw):
        res = self.literal_text if self.literal_text else ""
        if self.field_name is None:
            return res
        suffix = kw[self.field_name]
        if self.specifier:
            # If provided, enforce specifier
            regexp = re.compile(VALUE_PATTERNS[self.specifier])
            if not regexp.match(suffix):
                msg = f"Parameter '{self.field_name}' does not match specifier '{self.specifier}'"
                raise InvalidValue(msg)
        return res + suffix


# see https://github.com/python/cpython/blob/3.12/Lib/string.py
class Pattern:
    formatter = Formatter()

    def __init__(self, pattern: str, *fields: PatternField):
        self.pattern = pattern
        self.fields = fields

    @classmethod
    def from_string(cls, pattern: str) -> "Pattern":
        fields = []
        for literal_text, field_name, specifier, _ in cls.formatter.parse(pattern):
            fields.append(PatternField(literal_text, field_name, specifier))
        return Pattern(pattern, *fields)

    def fmt(self, kw):
        return "".join(f.fmt(kw) for f in self.fields)

    def __repr__(self):
        return f"<Pattern {self.pattern}>"
