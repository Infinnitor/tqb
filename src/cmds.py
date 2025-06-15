from argparse import Namespace, ArgumentParser
import csv
import consts
import parsing
from parsing import TaskQueue, Task, Constraint
from pprint import pprint
from tabulate import tabulate
import random
import os
import globals
import colorama
from colorama import Fore
import util
import fnmatch
import itertools
import colours


def create(parser: ArgumentParser, root: ArgumentParser):
    """Create a new task queue with default options"""

    def inner(args: Namespace):
        headers = args.headers.copy()

        msg_before = []
        msg_after = []

        if not headers:
            tq = TaskQueue.default()

            header_str = ", ".join(consts.DEFAULT_HEADERS)
            msg_before.append(
                f"creating taskqueue at {args.path} with default headers ({header_str})"
            )

        else:
            if consts.HEADER_ID_STRING not in headers:
                headers.insert(0, consts.HEADER_ID_STRING)

            tq = TaskQueue.from_headers(headers)

            header_str = ", ".join(headers)
            msg_before.append(
                f"creating taskqueue at {args.path} with headers ({header_str})"
            )

        parsing.serialize(args.path, tq)
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
        with open("logo-clr.txt") as fp:
            txt = fp.read()

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

    def inner(args: Namespace):
        taskq = parsing.deserialize(args.path)
        headers = args.columns if args.columns else taskq.get_display_headers()

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

            if args.sort is not None:
                assert (
                    args.sort in taskq.headers
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

                if args.ids:
                    table.append(str(task.geti(taskq.header_pk())))
                else:
                    table.append(task.to_display_row(headers))

            if not args.ids:
                col_widths = taskq.get_column_widths()

                message_after = (
                    [
                        f"output truncated to {TRUNCATE_LENGTH} of {TRUNCATE_LENGTH + num_truncated_tasks} entries"
                    ]
                    if globals.LS_OUTPUT_TRUNCATED
                    else [f"{len(table)} tasks"]
                )

                util.pretty_print_table(
                    table if table else [[]],
                    headers,
                    col_widths,
                    msg_before=["TASK QUEUE ^_^"],
                    msg_after=message_after,
                )
            else:
                print(" ".join(table))

    parser.add_argument("columns", nargs="*", help="columns to display")
    parser.add_argument("--header", action="store_true", help="just display the header")
    parser.add_argument(
        "-o", "--oldest", action="store_true", help="display older commands first"
    )
    parser.add_argument(
        "-a", "--all", action="store_true", help="display archived tasks"
    )

    parser.add_argument("-s", "--sort", default=None, help="sort by column")

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

    parser.add_argument("--ids", action="store_true", help="only output task ids")

    return inner


def add(parser: ArgumentParser, root: ArgumentParser):
    """Add a task with [description] to the task queue"""

    def inner(args: Namespace):
        taskq = parsing.deserialize(args.path)

        new_task = Task.new_task(args.description, taskq)
        taskq.add_task(new_task)

        util.pretty_print_table(
            [new_task.to_display_row()],
            taskq.headers,
            msg_after=["added task to queue :3"],
            indent_table=colours.Indents.ADD,
        )
        parsing.serialize(args.path, taskq)

    parser.add_argument("description", help="description of new task")

    return inner


def find(parser: ArgumentParser, root: ArgumentParser):
    """Find a task by id and display it"""

    def inner(args: Namespace):
        taskq = parsing.deserialize(args.path)

        task = taskq.find_or_fail(args.id)
        util.pretty_print_table(
            [task.to_display_row()],
            taskq.headers,
            msg_before=[f"entry for task with id {args.id}"],
        )

    parser.add_argument("id", type=int, help="of of task to edit")

    return inner


def update(parser: ArgumentParser, root: ArgumentParser):
    """Set a task property to a new value"""

    def inner(args: Namespace):
        taskq = parsing.deserialize(args.path)

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

        util.pretty_print_table(
            table,
            taskq.headers,
            msg_after=[
                f"updated id{'s' if len(args.ids) > 1 else ''} {', '.join(map(str, args.ids))}"
            ],
            indent_table=colours.Indents.UPDATE,
        )
        parsing.serialize(args.path, taskq)

    parser.add_argument("ids", type=int, nargs="+", help="id of task to edit")
    parser.add_argument("column", help="column to update")
    parser.add_argument("value", help="new value for column")

    return inner


def remove(parser: ArgumentParser, root: ArgumentParser):
    """Remove a task by id"""

    def inner(args: Namespace):
        taskq = parsing.deserialize(args.path)

        table = []
        for id in args.ids:
            taskq.find_or_fail(id)
            task = taskq.remove_task(id)

            table.append(task.to_display_row())

        tlen = len(table)
        plural = "s" if tlen > 1 else ""
        ids_string = " ".join(map(str, args.ids))
        util.pretty_print_table(
            table,
            taskq.headers,
            msg_after=[f"removed {tlen} task{plural} with id{plural} {ids_string}"],
            indent_table=colours.Indents.REMOVE,
        )

        parsing.serialize(args.path, taskq)

    parser.add_argument("ids", nargs="+", type=int, help="id of task to remove")

    return inner


def mark(parser: ArgumentParser, root: ArgumentParser):
    """Set a task Status"""

    def inner(args: Namespace):
        taskq = parsing.deserialize(args.path)

        status_col = taskq.header_status()
        archive_col = taskq.header_archive()

        table = []
        for id in args.ids:
            task = taskq.find_or_fail(id)
            task.update_column(status_col, args.value)
            if args.archive:
                task.update_column(archive_col, "True")

            table.append(task.to_display_row())

        util.pretty_print_table(
            table,
            taskq.headers,
            msg_after=[
                f"{len(args.ids)} task{'s' if len(args.ids) > 1 else ''} marked as {args.value}!"
            ],
            indent_table=colours.Indents.UPDATE,
        )
        parsing.serialize(args.path, taskq)

    parser.add_argument("ids", type=int, nargs="+", help="ids of task to edit")
    parser.add_argument("value", help="new status of task")
    parser.add_argument(
        "-a", "--archive", action="store_true", help="whether to archive task"
    )

    return inner


def archive(parser: ArgumentParser, root: ArgumentParser):
    """Archive (hide) tasks"""

    def inner(args: Namespace):
        taskq = parsing.deserialize(args.path)

        archive_col = taskq.header_archive()

        table = []
        for id in args.ids:
            task = taskq.find_or_fail(id)
            task.update_column(archive_col, str(args.undo))
            table.append(task.to_display_row())

        util.pretty_print_table(
            table,
            taskq.headers,
            msg_after=[
                f"{len(args.ids)} task{'s' if len(args.ids) > 1 else ''} archived :o"
            ],
            indent_table=colours.Indents.ARCHIVE if args.undo else colours.Indents.ARCHIVE_UNDO,
        )
        parsing.serialize(args.path, taskq)

    parser.add_argument("ids", nargs="+", type=int, help="ids of task to archive")
    parser.add_argument("-u", "--undo", action="store_false", help="undo archive")

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
        def inner(args: Namespace):
            target = args.target
            taskq = parsing.deserialize(args.path)

            assert target not in taskq.headers, f"column named {target} already exists"

            taskq.headers.append(target)
            for task in taskq.tasks:
                task.items[target] = ""

            taskq.constraints[target] = Constraint.empty(target)

            parsing.serialize(args.path, taskq)

            print(
                util.star_symbol_surround(
                    f"column {target} added", consts.STAR_MSG_OUTPUT_WIDTH
                )
            )

        sparser.add_argument("target", help="column name to add")
        return inner

    def move(sparser: ArgumentParser):
        def inner(args: Namespace):
            target = args.target
            taskq = parsing.deserialize(args.path)

            assert target in taskq.headers, "column named {target} does not exist"

            cidx = taskq.headers.index(target)
            taskq.headers.pop(cidx)
            taskq.headers.insert(args.index, target)

            parsing.serialize(args.path, taskq)

            print(
                util.star_symbol_surround(
                    f"column {target} moved to index {args.index}", consts.STAR_MSG_OUTPUT_WIDTH
                )
            )

        sparser.add_argument("target", help="column to move")
        sparser.add_argument("index", type=int, help="index to move column to (0 = start)")
        return inner

    def rename(sparser: ArgumentParser):
        def inner(args: Namespace):
            taskq = parsing.deserialize(args.path)
            old_name = args.target

            assert old_name in taskq.headers, "column named {target} does not exist"

            cidx = taskq.headers.index(old_name)
            taskq.headers[cidx] = args.name

            for task in taskq.tasks:
                col_value = task.items[old_name]
                del task.items[old_name]
                task.items[args.name] = col_value

            constraint = taskq.constraints[old_name]
            del taskq.constraints[old_name]
            taskq.constraints[args.name] = constraint

            parsing.serialize(args.path, taskq)

            print(
                util.star_symbol_surround(
                    f"column {old_name} renamed to {args.name}", consts.STAR_MSG_OUTPUT_WIDTH
                )
            )

        sparser.add_argument("target", help="column to rename")
        sparser.add_argument("name", help="new name of column")
        return inner

    def remove(sparser: ArgumentParser):
        def inner(args: Namespace):
            taskq = parsing.deserialize(args.path)
            target = args.target
            assert target in taskq.headers, "column named {target} does not exist"

            cidx = taskq.headers.index(target)
            taskq.headers.pop(cidx)

            for task in taskq.tasks:
                del task.items[target]

            del taskq.constraints[target]
            parsing.serialize(args.path, taskq)

            print(
                util.star_symbol_surround(
                    f"column {target} successfully removed", consts.STAR_MSG_OUTPUT_WIDTH
                )
            )

        sparser.add_argument("target", help="column to delete")
        return inner

    subcmd = parser.add_subparsers(required=True, help="constraint subcommands")

    for cmd_factory in [add, move, rename, remove]:
        parser = subcmd.add_parser(cmd_factory.__name__, help=cmd_factory.__doc__)
        func = cmd_factory(parser)
        parser.set_defaults(func=func)


def constraint(parser: ArgumentParser, root: ArgumentParser):
    """Subcommand for working with constraints"""

    def add(sparser: ArgumentParser):
        """Add constraint"""

        def inner(args: Namespace):
            taskq = parsing.deserialize(args.path)
            target = args.target
            assert taskq.find_constraint(target) is None, "constraint already exists"

            items = {}
            for pair in args.properties:
                k, _, v = pair.partition("=")
                items[k] = v

            items["HeaderName"] = target

            constraint = parsing.Constraint.kwargs(**items)
            taskq.add_constraint(constraint)
            parsing.serialize(args.path, taskq)

        sparser.add_argument("target", help="header name to add constraint to")
        sparser.add_argument("properties", nargs="+", help="properties to modify")

        return inner

    def alter(sparser: ArgumentParser):
        """Alter existing constraint"""

        def inner(args: Namespace):
            taskq = parsing.deserialize(args.path)
            target = args.target
            constraint = taskq.find_constraint(target)
            assert constraint is not None, "constraint does not exist, cannot alter"

            for pair in args.properties:
                k, _, v = pair.partition("=")
                constraint.__dict__[k] = v

            parsing.serialize(args.path, taskq)
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

        def inner(args: Namespace):
            taskq = parsing.deserialize(args.path)
            target = args.target
            column = args.constraint

            assert (
                target in taskq.constraints
            ), "constraint with HeaderName {target} could not be found"

            assert column in consts.CONSTRAINTS_HEADERS

            constraint = taskq.constraints[target]
            parsed_column = constraint.__dict__[column].split("|")
            parsed_column.extend(args.properties)
            constraint.__dict__[column] = "|".join(parsed_column)

            parsing.serialize(args.path, taskq)
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

        def inner(args: Namespace):
            taskq = parsing.deserialize(args.path)
            target = args.target

            assert (
                target in taskq.constraints
            ), "constraint with HeaderName {target} could not be found"
            del taskq.constraints[args.target]

            print(
                util.star_symbol_surround(
                    "constraint removed", consts.STAR_MSG_OUTPUT_WIDTH
                )
            )
            parsing.serialize(args.path, taskq)

        sparser.add_argument("target", help="header name of constraint to remove")

        return inner

    def ls(sparser: ArgumentParser):
        """Remove constraint"""

        def inner(args: Namespace):
            taskq = parsing.deserialize(args.path)
            headers = args.columns if args.columns else consts.CONSTRAINTS_HEADERS

            if args.header is True:
                util.pretty_print_table([headers])
                return

            table = []
            for constraint in taskq.constraints.values():
                table.append([constraint.__dict__[k] for k in headers])

            txt = tabulate(
                table,
                headers=headers,
                tablefmt="rounded_outline",
            )

            if globals.USE_LESS_FOR_OUTPUT:
                os.system(f'echo "{txt}" | less -SR')
            else:
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
    find,
    archive,
    remove,
    column,
    constraint,
    blueprint,
    help,
]
