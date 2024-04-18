import argparse
import logging
import json
from importlib.machinery import SourceFileLoader

from .exceptions import InterlinkedException
from .workflow import Workflow

try:
    import rich
    from rich.tree import Tree
except ImportError:
    rich = None

from interlinked import default_workflow, __version__


fmt = "%(levelname)s:%(asctime).19s: %(message)s"
logging.basicConfig(format=fmt)
logger = logging.getLogger("interlinked")


def run_cmd(args):
    wkf = find_workflow(args)

    config = load_conf(args.config)

    for target in args.targets:
        res = wkf.config(config).run(target)
        if args.show:
            print(res)


def load_conf(path):
    if path.endswith(".toml"):
        import toml
        return toml.load(path)
    elif path.endswith(".json"):
        return json.load(open(path))
    else:
        raise ValueError("File type not supported (should be json or toml)")


def find_workflow(args):
    src = args.source
    wkf_variable = None
    if ":" in src:
        src, wkf_variable = src.split(":", 1)
        assert isinstance(wkf_variable, Workflow)

    src = src.replace(".", "/")

    loader = SourceFileLoader(args.source, f"{src}.py")
    module = loader.load_module()
    if not wkf_variable:
        return default_workflow

    return getattr(module, wkf_variable)


def deps(args):
    if rich is None:
        msg = "Please install rich to display dependencies"
        exit(msg)

    # Instanciate child->parent dict
    wkf = find_workflow(args)
    deps = wkf.deps()

    # Find roots aka items without parents
    roots = set(deps) - set(p for c in deps for p in deps[c])
    # Build tree
    top_tree = Tree("/", hide_root=True)
    level = [(r, top_tree) for r in roots]
    while level:
        new_level = []
        for node, tree in sorted(level, key=lambda x: x[0]):
            subtree = tree.add(node)
            for child in deps[node]:
                new_level.append((child, subtree))
        level = new_level
    rich.print(top_tree)


def validate(args):
    wkf = find_workflow(args)
    try:
        wkf.validate()
    except InterlinkedException as e:
        exit("Error: " + str(e))
    print("ok")


def main():
    parser = argparse.ArgumentParser(
        prog="interlinked",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "source", help="ressource to load in the form of file_name (without the .py) "
        "or file_name:workflow_name",
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity"
    )
    subparsers = parser.add_subparsers(dest="command")

    parser_deps = subparsers.add_parser(
        "deps", description="Show dependencies")
    parser_deps.set_defaults(func=deps)

    parser_version = subparsers.add_parser(
        "version", description="Print version")
    parser_version.set_defaults(func=lambda a: print(__version__))

    parser_validate = subparsers.add_parser(
        "validate", description="Validate Workflow")
    parser_validate.add_argument(
        "-n", "--name", default="default_workflow", help="Workflow name",
    )
    parser_validate.set_defaults(func=validate)

    parser_run = subparsers.add_parser(
        "run", description="Print run")
    parser_run.add_argument(
        "-s", "--show", action="store_true", help="Show output"
    )
    parser_run.add_argument(
        "-c", "--config", help="Load parameters from config"
    )
    parser_run.add_argument(
        "targets", nargs="*", help="Run given targets"
    )
    parser_run.set_defaults(func=run_cmd)

    args = parser.parse_args()
    if args.verbose == 1:
        logger.setLevel("INFO")
    elif args.verbose > 1:
        logger.setLevel("DEBUG")

    if not args.command:
        parser.print_help()
        return
    args.func(args)
