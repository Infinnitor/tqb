import os
import globals
import consts
from argparse import ArgumentParser


def runner(parser: ArgumentParser, argv: list[str]):
    argp = parser

    parsed = argp.parse_args(argv)
    globals.USE_LESS_FOR_OUTPUT = parsed.less
    globals.QUIET_OPTION_SET = parsed.quiet

    if parsed.clear:
        os.system("clear")

    if parsed.help:
        parsed = argp.parse_args(argv + ["help"])
        parsed.func(parsed)
    elif hasattr(parsed, "func"):
        parsed.func(parsed)
    else:
        parsed = argp.parse_args(argv + [consts.DEFAULT_SUBCOMMAND])
        parsed.func(parsed)


def runner_with_handling(parser: ArgumentParser, argv: list[str]):
    try:
        runner(parser, argv)
    except AssertionError as e:
        parser.error(str(e))
