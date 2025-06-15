import globals
from tabulate import tabulate
import functools
from colorama import Fore
import os
import random
import consts


def get_terminal_size() -> tuple[int, int]:
    try:
        return os.get_terminal_size()
    except OSError:
        return consts.FALLBACK_TERMINAL_SIZE


def clr_surround_fore(txt, colour):
    return f"{colour}{txt}{Fore.RESET}"


def star_symbol_surround(msg, width):
    def stars(x):
        return " ".join([random.choice(consts.STAR_CHARACTER_CHOICE) for _ in range(x)])

    if len(msg) % 2 == 1 and width % 2 == 0:
        msg += " "

    msg = f"  {msg}  "
    padding = (width - len(msg)) // 4 + 1
    msg = f"{Fore.CYAN}{msg}{Fore.RESET}"

    fmt = stars(padding) + msg + stars(padding)
    return fmt


def find_visual_length_of_line(line):
    line_without_colours = functools.reduce(
        lambda acc, r: acc.replace(r, ""), Fore.__dict__.values(), line
    )
    return len(line_without_colours)


def pretty_print_table(
    table,
    headers=None,
    column_widths=None,
    style=None,
    msg_before=[],
    msg_after=[],
    indent_table="",
):

    def truncate_table_width(text):
        lines = text.split("\n")

        twidth, theight = get_terminal_size()
        truncated_lines = []

        for line in lines:
            if twidth < find_visual_length_of_line(line):
                target_idx = twidth
                target_text = line

                idx = 0
                visual_idx = 0
                while visual_idx < target_idx:
                    for r in Fore.__dict__.values():
                        if target_text[idx:].startswith(r):
                            idx += len(r)
                    visual_idx += 1
                    idx += 1

                truncated_lines.append(line[:idx])
            else:
                truncated_lines.append(line)

        return "\n".join(truncated_lines)

    def style_txt_process(text):
        BORDERS = ["─", "┴", "┼", "┬", "├", "│", "┤", "|", "┘", "┐", "┌", "└"]

        match style:
            case _:
                lines = text.split("\n")
                output = []

                for idx, line in enumerate(lines):
                    if idx % 2 == 0:
                        output.append(clr_surround_fore(line, Fore.BLACK))
                    else:
                        text = line
                        for r in BORDERS:
                            text = text.replace(r, clr_surround_fore(r, Fore.BLACK))

                        output.append(text)

                return "\n".join(output)

    prettify_fn = tabulate

    if headers:
        headers_clr = [clr_surround_fore(h, Fore.GREEN) for h in headers]
        prettify_fn = functools.partial(prettify_fn, headers=headers_clr)

    if not column_widths:
        if headers:
            column_widths = [None for _ in range(len(headers))]
        else:
            column_widths = [None for _ in range(len(table[0]))]

    txt = prettify_fn(
        table if table else [[]], tablefmt="simple_grid", maxcolwidths=column_widths
    )

    prettified = style_txt_process(txt)
    if indent_table:
        lines = [
            f"{indent_table} {line}"
            for line in prettified.split("\n")
        ]
        prettified = "\n".join(lines)

    prettified = truncate_table_width(prettified) + Fore.RESET
    table_visual_width = find_visual_length_of_line(prettified.split("\n")[0])

    for msg in msg_before:
        print(star_symbol_surround(msg, table_visual_width))

    print(prettified)

    for msg in msg_after:
        print(star_symbol_surround(msg, table_visual_width))
