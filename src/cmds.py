import os
import csv
import random
import globals
import fnmatch
import itertools
import shlex
import program

from typing import Callable
from argparse import Namespace, ArgumentParser

import consts
import parsing
import colours
import util
import logo
from tasks import Task, TaskQueue
from constraints import Constraint
from config import Config, ConfigPair

import pyperclip
from colorama import Fore


def tqb_serialize(func: Callable):
    def inner(args: Namespace):
        try:
            taskq = parsing.deserialize(args.path)
        except FileNotFoundError:
            raise AssertionError(f"taskqueue not found '{args.path}'")

        globals.USE_LESS_FOR_OUTPUT = args.less
        globals.QUIET_OPTION_SET = bool(taskq.config.get_value("GlobalQuiet", False))

        func(taskq, args)
        parsing.serialize(args.path, taskq)

    return inner


def create(parser: ArgumentParser, root: ArgumentParser):
    """Create a new task queue with default options"""

    def inner(args: Namespace):
        headers = args.headers.copy()

        msg_before = []
        msg_after = []

        assert not os.path.exists(args.path), "taskqueue already exists at specified path"

        if not headers:
            tq = TaskQueue.default()

            header_str = ", ".join(consts.DEFAULT_HEADERS)
            msg_before.append(
                f"creating taskqueue at '{args.path}' with default headers ({header_str})"
            )

        else:
            tq = TaskQueue.from_headers(headers)

            header_str = ", ".join(headers)
            msg_before.append(
                f"creating taskqueue at {args.path} with headers ({header_str})"
            )

        parsing.serialize(args.path, tq)

        if not globals.QUIET_OPTION_SET:
            util.pretty_print_table(
                [], tq.headers, msg_before=msg_before, msg_after=msg_after
            )

    parser.add_argument(
        "headers", nargs="*", help="headers to include in the new taskqueue"
    )
    return inner


def help(parser: ArgumentParser, root: ArgumentParser):
    """Print the program help text"""

    def inner(args: Namespace):
        txt = logo.LOGO

        colours = [
            Fore.GREEN,
            Fore.MAGENTA,
            Fore.RED,
            Fore.YELLOW,
            Fore.BLUE,
            Fore.CYAN,
        ]

        clr1, clr2, clr3 = (
            colours.pop(random.randint(0, len(colours) - 1)),
            colours.pop(random.randint(0, len(colours) - 1)),
            colours.pop(random.randint(0, len(colours) - 1)),
        )

        txt = txt.replace("<CLR1>", clr1)
        txt = txt.replace("<CLR2>", clr2)
        txt = txt.replace("<CLR3>", clr3)

        print(txt + Fore.RESET)

        root.print_help()

    return inner


def ls(parser: ArgumentParser, root: ArgumentParser):
    """Display the task queue"""

    @tqb_serialize
    def inner(taskq: TaskQueue, args: Namespace):
        headers = (
            taskq.headers
            if args.show_all_columns
            else args.columns if args.columns else taskq.get_display_headers()
        )

        if args.header is True:
            util.pretty_print_table(
                [headers],
                msg_before=["TASK QUEUE"],
                msg_after=["displaying only headers"],
            )

        else:
            assert all(h in taskq.headers for h in headers), "invalid column(s) passed"

            twidth, theight = util.get_terminal_size()

            TRUNCATE_LENGTH = max((theight // 2) - 3, 2) or consts.LS_TRUNCATE_LENGTH

            table = []
            tasks_list = taskq.tasks
            ids_list = []

            if args.sort is not None:
                assert taskq.smart_header_match(
                    args.sort
                ), f"sorting column {args.sort} is not a valid header"
                tasks_list = sorted(
                    tasks_list, key=lambda x: x.geti(args.sort), reverse=True
                )

            if not args.oldest:
                tasks_list = reversed(tasks_list)

            num_truncated_tasks = 0
            for idx, task in enumerate(tasks_list):
                if not args.all and task.is_archived():
                    continue

                if (
                    len(table) >= TRUNCATE_LENGTH
                    and not args.all
                    and not args.notruncate
                ):
                    globals.LS_OUTPUT_TRUNCATED = True
                    num_truncated_tasks += 1
                    continue

                if args.whereor:
                    parititioned = [clause.partition("=") for clause in args.whereor]
                    if not any(task.matchi(c, v) for c, _, v in parititioned):
                        continue

                if args.where:
                    parititioned = [clause.partition("=") for clause in args.where]
                    if not all(task.matchi(c, v) for c, _, v in parititioned):
                        continue

                if args.search is not None:
                    pat = f"*{args.search.lower()}*"
                    if not any(
                        fnmatch.fnmatch(str(value).lower(), pat)
                        for value in task.items.values()
                    ):
                        continue

                table.append(task.to_display_row(headers))
                ids_list.append(str(task.id))

            if args.copyids:
                pyperclip.copy(" ".join(ids_list))

            if not args.ids:
                col_widths = taskq.get_column_widths()

                message_after = (
                    [
                        f"output truncated to {TRUNCATE_LENGTH} of {TRUNCATE_LENGTH + num_truncated_tasks} entries"
                    ]
                    if globals.LS_OUTPUT_TRUNCATED
                    else [f"{len(table)} tasks"] if table else ["no tasks in queue ^^"]
                )

                util.pretty_print_table(
                    table if table else [[]],
                    headers,
                    col_widths,
                    msg_before=["TASK QUEUE ^_^"],
                    msg_after=message_after,
                )
            else:
                print(" ".join(ids_list))

    parser.add_argument("columns", nargs="*", help="columns to display")
    parser.add_argument("--header", action="store_true", help="just display the header")
    parser.add_argument(
        "-o", "--oldest", action="store_true", help="display older commands first"
    )
    parser.add_argument(
        "-a", "--all", action="store_true", help="display archived tasks"
    )

    parser.add_argument("--sort", default=None, help="sort by column")

    parser.add_argument(
        "-nt", "--notruncate", action="store_true", help="do not truncate output"
    )

    parser.add_argument(
        "-wo", "--whereor", nargs="+", help="column=value filter clause (one must pass)"
    )

    parser.add_argument(
        "-w",
        "--where",
        nargs="+",
        help="column=value filter clause (all must pass)",
    )

    parser.add_argument(
        "--search",
        default=None,
        help="search for value in across all columns",
    )

    parser.add_argument(
        "--show-all-columns",
        action="store_true",
        help="show all columns, including hidden ones",
    )

    parser.add_argument("--ids", action="store_true", help="only output task ids")
    parser.add_argument(
        "--copyids", action="store_true", help="copy ids of tasks to clipboard"
    )

    return inner


def add(parser: ArgumentParser, root: ArgumentParser):
    """Add a task with [description] to the task queue"""

    @tqb_serialize
    def inner(taskq: TaskQueue, args: Namespace):
        new_task = Task.new_task(args.description, taskq)
        taskq.add_task(new_task)

        for property in args.properties:
            prop, _, value = property.partition("=")
            new_task.update_column(prop, value)

        if not globals.QUIET_OPTION_SET:
            util.pretty_print_table(
                [new_task.to_display_row()],
                taskq.get_display_headers(),
                msg_after=["added task to queue :3"],
                indent_table=colours.Indents.ADD,
            )

    parser.add_argument("description", help="description of new task")
    parser.add_argument("properties", nargs="*", help="additional properties to assign")

    return inner


def show(parser: ArgumentParser, root: ArgumentParser):
    """Find a task by id and display it"""

    @tqb_serialize
    def inner(taskq: TaskQueue, args: Namespace):
        task = taskq.find_or_fail(args.id)
        table = []
        for header, value in task.items.items():
            coloured_value = taskq.find_constraint_fallback(header).apply_colour(value)
            table.append([util.clr_surround_fore(header, Fore.GREEN), coloured_value])

        util.pretty_print_table(
            table,
            msg_before=[f"entry for task with id {args.id}"],
        )

    parser.add_argument("id", type=int, help="of of task to edit")

    return inner


def update(parser: ArgumentParser, root: ArgumentParser):
    """Set a task property to a new value"""

    @tqb_serialize
    def inner(taskq: TaskQueue, args: Namespace):
        assert (
            taskq.smart_header_match(args.column) is not None
        ), f"column '{args.column}' is invalid"

        column = taskq.smart_header_match(args.column)
        assert column, f"could not find matching column for {args.column}"

        table = []
        for id in args.ids:
            task = taskq.find_or_fail(id)
            task.update_column(column, args.value)
            table.append(task.to_display_row())

        if not globals.QUIET_OPTION_SET:
            util.pretty_print_table(
                table,
                taskq.get_display_headers(),
                msg_after=[
                    f"updated id{'s' if len(args.ids) > 1 else ''} {', '.join(map(str, args.ids))}"
                ],
                indent_table=colours.Indents.UPDATE,
            )

    parser.add_argument("ids", type=int, nargs="+", help="id of task to edit")
    parser.add_argument("column", help="column to update")
    parser.add_argument("value", help="new value for column")

    return inner


def remove(parser: ArgumentParser, root: ArgumentParser):
    """Remove a task by id"""

    @tqb_serialize
    def inner(taskq: TaskQueue, args: Namespace):
        table = []
        for id in args.ids:
            taskq.find_or_fail(id)
            task = taskq.remove_task(id)

            table.append(task.to_display_row())

        tlen = len(table)
        plural = "s" if tlen > 1 else ""
        ids_string = " ".join(map(str, args.ids))

        if not globals.QUIET_OPTION_SET:
            util.pretty_print_table(
                table,
                taskq.get_display_headers(),
                msg_after=[f"removed {tlen} task{plural} with id{plural} {ids_string}"],
                indent_table=colours.Indents.REMOVE,
            )

    parser.add_argument("ids", nargs="+", type=int, help="id of task to remove")

    return inner


def mark(parser: ArgumentParser, root: ArgumentParser):
    """Set a task Status"""

    @tqb_serialize
    def inner(taskq: TaskQueue, args: Namespace):
        status_col = taskq.header_status()

        constraint = taskq.find_constraint_fallback(status_col)
        constrained_value = constraint.constrain_variant(args.value)

        table = []
        for id in args.ids:
            task = taskq.find_or_fail(id)
            task.update_column(status_col, constrained_value)
            if args.archive:
                archive_col = taskq.header_archive()
                task.update_column(archive_col, "True")

            table.append(task.to_display_row())

        if not globals.QUIET_OPTION_SET:
            util.pretty_print_table(
                table,
                taskq.get_display_headers(),
                msg_after=[
                    f"{len(args.ids)} task{'s' if len(args.ids) > 1 else ''} marked as {constrained_value}!"
                ],
                indent_table=(
                    colours.Indents.MARK
                    if not args.archive
                    else colours.Indents.MARK_ARCHIVE
                ),
            )

    parser.add_argument("ids", type=int, nargs="+", help="ids of task to edit")
    parser.add_argument("value", help="new status of task")
    parser.add_argument(
        "-a", "--archive", action="store_true", help="whether to archive task"
    )

    return inner


def archive(parser: ArgumentParser, root: ArgumentParser):
    """Archive (hide) tasks"""

    @tqb_serialize
    def inner(taskq: TaskQueue, args: Namespace):
        archive_col = taskq.header_archive()

        table = []
        for id in args.ids:
            task = taskq.find_or_fail(id)
            task.update_column(archive_col, str(args.unarchive))
            table.append(task.to_display_row())

        if not globals.QUIET_OPTION_SET:
            util.pretty_print_table(
                table,
                taskq.get_display_headers(),
                msg_after=[
                    f"{len(args.ids)} task{'s' if len(args.ids) > 1 else ''} archived :o"
                ],
                indent_table=(
                    colours.Indents.ARCHIVE
                    if args.unarchive
                    else colours.Indents.ARCHIVE_UNDO
                ),
            )

    parser.add_argument("ids", nargs="+", type=int, help="ids of task to archive")
    parser.add_argument("-u", "--unarchive", action="store_false", help="unarchive")

    return inner


def alias(parser: ArgumentParser, root: ArgumentParser):
    """Use an alias defined with config"""

    @tqb_serialize
    def inner(taskq: TaskQueue, args: Namespace):
        alias = next(
            (
                a
                for a in taskq.config.get_all(consts.CONFIG_ALIAS_NAMESPACE)
                if a.Value == args.name
            ),
            None,
        )
        assert alias, f"could not find alias with name '{args.name}'"
        assert alias.Opt, "could not run alias, is empty"

        cmd_txt = alias.Opt
        for idx, arg in enumerate(args.arguments):
            replace_str = f"${idx}"
            if arg.startswith("-"):
                cmd_txt += f" {arg} "
            elif replace_str in cmd_txt:
                cmd_txt = cmd_txt.replace(replace_str, arg)
            else:
                cmd_txt += f" {arg} "

        run_args = shlex.split(cmd_txt)
        parsed = root.parse_args(run_args)
        if hasattr(parsed, "func"):
            assert (
                parsed.func.__name__ != "alias"
            ), "do NOT recursively run alias commands lol"

        program.runner(root, run_args)

    parser.add_argument("name", help="name of the alias to use")
    parser.add_argument(
        "arguments", nargs="*", help="additional arguments to pass to the alias"
    )

    return inner


def blueprint(parser: ArgumentParser, root: ArgumentParser):
    """Dump constraint and header information of taskqueue to STDOUT"""

    def inner(args: Namespace):
        with open(args.path, "r") as fp:
            lines = fp.readlines()

        it = iter(lines)
        blueprint = list(
            itertools.takewhile(lambda x: not x.startswith(consts.CONSTRAINTS_END), it)
        )
        blueprint.append(consts.CONSTRAINTS_END + "\n")
        blueprint.append(next(it))

        print("".join(blueprint))

    return inner


def column(parser: ArgumentParser, root: ArgumentParser):
    """Subcommand for adding, moving, renaming and removing columns"""

    def add(sparser: ArgumentParser):
        @tqb_serialize
        def inner(taskq: TaskQueue, args: Namespace):
            target = args.target

            assert target not in taskq.headers, f"column named {target} already exists"

            taskq.headers.append(target)
            for task in taskq.tasks:
                task.items[target] = ""

            taskq.constraints[target] = Constraint.empty(target)

            if not globals.QUIET_OPTION_SET:
                print(
                    util.star_symbol_surround(
                        f"column {target} added", consts.STAR_MSG_OUTPUT_WIDTH
                    )
                )

        sparser.add_argument("target", help="column name to add")
        return inner

    def move(sparser: ArgumentParser):
        @tqb_serialize
        def inner(taskq: TaskQueue, args: Namespace):
            target = args.target

            assert target in taskq.headers, "column named {target} does not exist"

            cidx = taskq.headers.index(target)
            taskq.headers.pop(cidx)
            taskq.headers.insert(args.index, target)

            if not globals.QUIET_OPTION_SET:
                print(
                    util.star_symbol_surround(
                        f"column {target} moved to index {args.index}",
                        consts.STAR_MSG_OUTPUT_WIDTH,
                    )
                )

        sparser.add_argument("target", help="column to move")
        sparser.add_argument(
            "index", type=int, help="index to move column to (0 = start)"
        )
        return inner

    def rename(sparser: ArgumentParser):
        @tqb_serialize
        def inner(taskq: TaskQueue, args: Namespace):
            old_name = args.target

            assert old_name in taskq.headers, "column named {target} does not exist"

            cidx = taskq.headers.index(old_name)
            taskq.headers[cidx] = args.name

            for task in taskq.tasks:
                col_value = task.items[old_name]
                del task.items[old_name]
                task.items[args.name] = col_value

            constraint = taskq.find_constraint_fallback(old_name)
            constraint.HeaderName = args.name

            if taskq.find_constraint(old_name):
                del taskq.constraints[old_name]

            taskq.constraints[args.name] = constraint

            if not globals.QUIET_OPTION_SET:
                print(
                    util.star_symbol_surround(
                        f"column {old_name} renamed to {args.name}",
                        consts.STAR_MSG_OUTPUT_WIDTH,
                    )
                )

        sparser.add_argument("target", help="column to rename")
        sparser.add_argument("name", help="new name of column")
        return inner

    def remove(sparser: ArgumentParser):
        """Remove column"""

        @tqb_serialize
        def inner(taskq: TaskQueue, args: Namespace):
            target = args.target
            assert target in taskq.headers, "column named {target} does not exist"

            cidx = taskq.headers.index(target)
            taskq.headers.pop(cidx)

            for task in taskq.tasks:
                del task.items[target]

            if taskq.find_constraint(target):
                del taskq.constraints[target]

            if not globals.QUIET_OPTION_SET:
                print(
                    util.star_symbol_surround(
                        f"column {target} successfully removed",
                        consts.STAR_MSG_OUTPUT_WIDTH,
                    )
                )

        sparser.add_argument("target", help="column to delete")
        return inner

    subcmd = parser.add_subparsers(required=True, help="constraint subcommands")

    for cmd_factory in [add, move, rename, remove]:
        parser = subcmd.add_parser(cmd_factory.__name__, help=cmd_factory.__doc__)
        func = cmd_factory(parser)
        parser.set_defaults(func=func)


def config(parser: ArgumentParser, root: ArgumentParser):
    """Subcommand for working with aliases"""

    def ls(sparser: ArgumentParser):
        """List config entries"""

        @tqb_serialize
        def inner(taskq: TaskQueue, args: Namespace):
            headers = consts.CONFIG_HEADERS

            util.pretty_print_table(
                [cfg.serialize() for cfg in taskq.config.configs],
                headers,
                msg_before=["config values"],
                msg_after=[f"{len(taskq.config.configs)} entries"],
            )

        return inner

    def add(sparser: ArgumentParser):
        """Add config entry"""

        @tqb_serialize
        def inner(taskq: TaskQueue, args: Namespace):
            cfg = ConfigPair(args.key, args.value, args.opt)
            for pair in taskq.config.get_all(cfg.Key):
                assert (
                    cfg.Value != pair.Value
                ), f"duplicate key found for {cfg}, cannot insert"

            taskq.config.add_config_pair(cfg)

            if not globals.QUIET_OPTION_SET:
                print(
                    util.star_symbol_surround(
                        "config added", consts.STAR_MSG_OUTPUT_WIDTH
                    )
                )

        sparser.add_argument("key", help="key")
        sparser.add_argument("value", help="value")
        sparser.add_argument("opt", nargs="?", default="", help="additional options")

        return inner

    def remove(sparser: ArgumentParser):
        """Add config entry"""

        @tqb_serialize
        def inner(taskq: TaskQueue, args: Namespace):
            for idx, cfg in enumerate(taskq.config.configs):
                if cfg.Key == args.key and cfg.Value == args.value:
                    taskq.config.configs.pop(idx)
                    break

            if not globals.QUIET_OPTION_SET:
                print(
                    util.star_symbol_surround(
                        "config removed", consts.STAR_MSG_OUTPUT_WIDTH
                    )
                )

        sparser.add_argument("key", help="namespace of config")
        sparser.add_argument("value", help="value of config")

        return inner

    subcmd = parser.add_subparsers(required=True, help="config subcommands")

    for cmd_factory in [ls, add, remove]:
        parser = subcmd.add_parser(cmd_factory.__name__, help=cmd_factory.__doc__)
        func = cmd_factory(parser)
        parser.set_defaults(func=func)


def constraint(parser: ArgumentParser, root: ArgumentParser):
    """Subcommand for working with constraints"""

    def add(sparser: ArgumentParser):
        """Add constraint"""

        @tqb_serialize
        def inner(taskq: TaskQueue, args: Namespace):
            target = args.target
            assert taskq.find_constraint(target) is None, "constraint already exists"

            items = {}
            for pair in args.properties:
                k, _, v = pair.partition("=")
                items[k] = v

            items["HeaderName"] = target

            constraint = parsing.Constraint.kwargs(**items)
            taskq.add_constraint(constraint)

        sparser.add_argument("target", help="header name to add constraint to")
        sparser.add_argument("properties", nargs="+", help="properties to modify")

        return inner

    def alter(sparser: ArgumentParser):
        """Alter existing constraint"""

        @tqb_serialize
        def inner(taskq: TaskQueue, args: Namespace):
            target = args.target
            constraint = taskq.find_constraint(target)
            assert constraint is not None, "constraint does not exist, cannot alter"

            for pair in args.properties:
                k, _, v = pair.partition("=")
                constraint.__dict__[k] = v

            if not globals.QUIET_OPTION_SET:
                print(
                    util.star_symbol_surround(
                        "constraint altered", consts.STAR_MSG_OUTPUT_WIDTH
                    )
                )

        sparser.add_argument("target", help="header name to add constraint to")
        sparser.add_argument("properties", nargs="+", help="properties to modify")

        return inner

    def append(sparser: ArgumentParser):
        """Add additional value to group constraints"""

        @tqb_serialize
        def inner(taskq: TaskQueue, args: Namespace):
            target = args.target
            column = args.constraint

            assert (
                target in taskq.constraints
            ), "constraint with HeaderName {target} could not be found"

            assert column in consts.CONSTRAINTS_HEADERS

            constraint = taskq.find_constraint_fallback(target)
            parsed_column = constraint.__dict__[column].split("|")
            parsed_column.extend(args.properties)
            constraint.__dict__[column] = "|".join(parsed_column)
            taskq.constraints[target] = constraint

            if not globals.QUIET_OPTION_SET:
                print(
                    util.star_symbol_surround(
                        "constraint properties appended", consts.STAR_MSG_OUTPUT_WIDTH
                    )
                )

        sparser.add_argument("target", help="header name to add constraint to")
        sparser.add_argument("constraint", help="constraint column to modify")
        sparser.add_argument("properties", nargs="+", help="properties to modify")

        return inner

    def remove(sparser: ArgumentParser):
        """Remove constraint"""

        @tqb_serialize
        def inner(taskq: TaskQueue, args: Namespace):
            target = args.target

            assert (
                target in taskq.constraints
            ), "constraint with HeaderName {target} could not be found"
            del taskq.constraints[args.target]

            if not globals.QUIET_OPTION_SET:
                print(
                    util.star_symbol_surround(
                        "constraint removed", consts.STAR_MSG_OUTPUT_WIDTH
                    )
                )

        sparser.add_argument("target", help="header name of constraint to remove")

        return inner

    def ls(sparser: ArgumentParser):
        """Remove constraint"""

        @tqb_serialize
        def inner(taskq: TaskQueue, args: Namespace):
            headers = args.columns if args.columns else consts.CONSTRAINTS_HEADERS

            if args.header is True:
                util.pretty_print_table([headers])
                return

            table = []
            for constraint in taskq.constraints.values():
                table.append([constraint.__dict__[k] for k in headers])

            util.pretty_print_table(table, headers)

        sparser.add_argument("columns", nargs="*", help="columns to display")
        sparser.add_argument(
            "--header", action="store_true", help="just display the header"
        )

        return inner

    subcmd = parser.add_subparsers(required=True, help="constraint subcommands")

    for cmd_factory in [add, alter, remove, ls, append]:
        parser = subcmd.add_parser(cmd_factory.__name__, help=cmd_factory.__doc__)
        func = cmd_factory(parser)
        parser.set_defaults(func=func)


COMMANDS = [
    create,
    ls,
    add,
    update,
    mark,
    show,
    archive,
    remove,
    column,
    constraint,
    alias,
    config,
    blueprint,
    help,
]
