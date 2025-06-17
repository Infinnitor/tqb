import os
import sys
import pytest

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


@setup_create_teardown
def test_cmd_show(runner):
    runner(argsd("add", "test"))
    ids = runner(argsd("ls", "--ids"), capture=True)
    runner(argsd("show", ids))  # AssertionError on find_or_fail


@setup_create_teardown
def test_cmd_show_fail(runner):
    with pytest.raises(AssertionError):
        runner(argsd("show", "1000"))


@setup_create_teardown
def test_cmd_remove(runner):
    runner(argsd("add", "test"))
    ids_output = runner(argsd("ls", "--ids"), capture=True)
    assert ids_output != ""

    runner(argsd("remove", ids_output))
    output = runner(argsd("ls", "--ids"), capture=True)
    assert output == ""


@setup_create_teardown
def test_cmd_remove_fail(runner):
    with pytest.raises(AssertionError):
        runner(argsd("remove", "1001010"))


@setup_create_teardown
def test_cmd_update(runner):
    runner(argsd("add", "test"))
    first = runner(argsd("ls"), capture=True)
    assert first != ""

    runner(argsd("update", "1", "task", "test2"))
    second = runner(argsd("ls"), capture=True)
    assert second != ""
    assert first != second


@setup_create_teardown
def test_cmd_update_fail(runner):
    with pytest.raises(AssertionError):
        runner(argsd("update", "1001", "task", "test2"))


@setup_create_teardown
def test_cmd_mark(runner):
    runner(argsd("add", "test", "Status=Not Started"))
    first = runner(argsd("ls"), capture=True)
    assert first != ""

    runner(argsd("mark", "1", "Done"))
    second = runner(argsd("ls"), capture=True)
    assert second != ""
    assert first != second


@setup_create_teardown
def test_cmd_mark_archive(runner):
    runner(argsd("add", "test", "Status=Not Started"))

    runner(argsd("mark", "1", "Done", "-a"))
    second = runner(argsd("ls", "--ids"), capture=True)
    assert second == ""


@setup_create_teardown
def test_cmd_mark_fail(runner):
    runner(argsd("add", "test", "Status=Not Started"))

    with pytest.raises(AssertionError):
        runner(argsd("mark", "1002", "Done", "-a"))


@setup_create_teardown
def test_cmd_archive(runner):
    runner(argsd("add", "test"))

    output = runner(argsd("archive", "1"), capture=True)
    output = runner(argsd("ls", "--ids"), capture=True)
    assert output == ""


@setup_create_teardown
def test_cmd_unarchive(runner):
    runner(argsd("add", "test"))

    runner(argsd("archive", "1"))
    output = runner(argsd("ls", "--ids"), capture=True)
    assert output == ""

    runner(argsd("archive", "1", "--unarchive"))
    output = runner(argsd("ls", "--ids"), capture=True)
    assert output != ""


@setup_create_teardown
def test_cmd_archive_fail(runner):
    runner(argsd("add", "test"))

    with pytest.raises(AssertionError):
        runner(argsd("archive", "1002"))
