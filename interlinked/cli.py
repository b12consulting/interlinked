import argparse
import logging
from collections import defaultdict

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

    # Create parent-child structure
    children = defaultdict(list)
    for pattern in wkf.router.routes:
        item = wkf.router.get(pattern)
        deps = item.dependencies.values()
        if not deps:
            children[pattern] = []
        else:
            for dep in deps:
                children[pattern].append(dep)

    # Find roots
    roots = set(children) - set(c for p in children for c in children[p])
    # Build tree
    top_tree = Tree("/", hide_root=True)
    level = [(r, top_tree) for r in roots]
    while level:
        new_level = []
        for node, tree in sorted(level, key=lambda x: x[0]):
            subtree = tree.add(node)
            for child in children[node]:
                new_level.append((child, subtree))
        level = new_level
    rich.print(top_tree)


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
