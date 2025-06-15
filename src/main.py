import sys
import argparse
from argparse import ArgumentParser
import cmds
import consts
import globals
import os


def program_args() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog=consts.APP_NAME)
    root.add_argument("--path", nargs="?", default=consts.DEFAULT_PATH, help="path to task queue file")
    root.add_argument("-v", "--version", action="version", version=consts.APP_VERSION_STRING, help="print version")
    root.add_argument("--less", action="store_true", help="use less to display output")
    root.add_argument("-c", "--clear", action="store_true", help="clear terminal before displaying task queue")
    subcmd = root.add_subparsers(help="subcommands", dest="subcommand")

    for cmd_factory in cmds.COMMANDS:
        parser = subcmd.add_parser(cmd_factory.__name__, help=cmd_factory.__doc__)
        func = cmd_factory(parser, root)

        if func is not None:
            parser.set_defaults(func=func)

    return root


def main(argv):
    argp = program_args()

    parsed = argp.parse_args(argv[1:])
    globals.USE_LESS_FOR_OUTPUT = parsed.less

    if parsed.clear:
        os.system("clear")

    if hasattr(parsed, "func"):
        parsed.func(parsed)
    else:
        parsed = argp.parse_args(argv[1:] + [consts.DEFAULT_SUBCOMMAND])
        parsed.func(parsed)


if __name__ == "__main__":
    main(sys.argv)
