import sys
import argparse
from argparse import ArgumentParser
import cmds
import consts
import globals
import os
import program


def program_argument_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog=consts.APP_NAME, add_help=False)
    root.add_argument("-h", "--help", action="store_true", help="show the help message")
    root.add_argument("-p", "--path", default=consts.DEFAULT_PATH, help=f"path to task queue file (default: {consts.DEFAULT_PATH})")
    root.add_argument("-v", "--version", action="version", version=consts.APP_VERSION_STRING, help="print version")
    root.add_argument("-c", "--clear", action="store_true", help="clear terminal before displaying task queue")
    root.add_argument("-q", "--quiet", action="store_true", help="do not output status messages")
    root.add_argument("--less", action="store_true", help="use 'less' to display output")
    subcmd = root.add_subparsers(help="subcommands", dest="subcommand")

    for cmd_factory in cmds.COMMANDS:
        parser = subcmd.add_parser(cmd_factory.__name__, help=cmd_factory.__doc__)
        func = cmd_factory(parser, root)

        if func is not None:
            parser.set_defaults(func=func)

    return root


def main(argv: list[str]):
    program.runner_with_handling(program_argument_parser(), argv[1:])


if __name__ == "__main__":
    main(sys.argv)
