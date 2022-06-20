import argparse
import logging

from .workflow import Workflow
from .exceptions import InterlinkedException

try:
    import rich
    from rich.tree import Tree
except ImportError:
    rich = None

from interlinked import run, default_workflow, __version__


fmt = "%(levelname)s:%(asctime).19s: %(message)s"
logging.basicConfig(format=fmt)
logger = logging.getLogger("interlinked")


def run_cmd(args):
    for target in args.targets:
        res = run(target)
        if args.show:
            print(res)


def deps(wkf):
    if rich is None:
        msg = "Please install rich to display dependencies"
        exit(msg)

    # Instanciate child->parent dict
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
    wkf = Workflow.get(args.name)
    if not wkf:
        exit(f"Workflow '{args.name}' not found")
    try:
        wkf.validate()
    except InterlinkedException as e:
        exit("Error: " + str(e))
    print("ok")

def main(wkf=default_workflow):

    parser = argparse.ArgumentParser(
        prog="interlinked",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity"
    )
    subparsers = parser.add_subparsers(dest="command")

    parser_deps = subparsers.add_parser(
        "deps", description="Show dependencies")
    parser_deps.set_defaults(func=lambda a: deps(wkf))

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
