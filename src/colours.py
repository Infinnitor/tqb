from enum import StrEnum
from colorama import Fore


class Indents(StrEnum):
    ADD = f"{Fore.GREEN}==+{Fore.RESET}"
    UPDATE = f"{Fore.YELLOW}==>{Fore.RESET}"
    MARK = f"{Fore.YELLOW}==~{Fore.RESET}"
    MARK_ARCHIVE = f"{Fore.MAGENTA}==~{Fore.RESET}"

    REMOVE = f"{Fore.RED}XXX{Fore.RESET}"
    ARCHIVE = f"{Fore.MAGENTA}<@@{Fore.RESET}"
    ARCHIVE_UNDO = f"{Fore.MAGENTA}@@>{Fore.RESET}"
