import sys
import os
import shutil
from functools import partial

from io import StringIO

SRCPATH = "/src/"
TEST_QUEUE_PATH = "test/res/queue.csv"
TQB_CREATION_COMMAND = ("--path", TEST_QUEUE_PATH, "create")
TQB_DEFAULT_ARGS = ("--path", TEST_QUEUE_PATH)

TEST_RES_PATH = "test/res/"

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + SRCPATH)

from main import program_argument_parser
import program


def setup_teardown(func):
    def inner():
        os.makedirs(TEST_RES_PATH, exist_ok=True)

        def runner(args, capture=False):
            if capture:
                with StdoutCapture() as output:
                    program.runner(program_argument_parser(), args)
                    return output
            else:
                program.runner(program_argument_parser(), args)

        func(runner)
        shutil.rmtree(TEST_RES_PATH)

    return inner


def create_default(func):
    def inner(runner):
        runner(TQB_CREATION_COMMAND)
        func(runner)
    return inner


def setup_create_teardown(func):
    return setup_teardown(create_default(func))


def argsd(*args: list[str]):
    return TQB_DEFAULT_ARGS + args


class StdoutCapture(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout
