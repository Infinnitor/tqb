import os
import sys
from base import (
    argsd,
    setup_teardown,
    setup_create_teardown,
    StdoutCapture,
    TEST_QUEUE_PATH,
)


@setup_teardown
def test_cmd_create(runner):
    runner(["--path", TEST_QUEUE_PATH, "create"])
    assert os.path.exists(TEST_QUEUE_PATH)


@setup_create_teardown
def test_cmd_add(runner):
    runner(argsd("add", "test"))
    output = runner(argsd("ls", "--ids"), capture=True)
    assert output != ""
