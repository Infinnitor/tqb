from dataclasses import dataclass
import csv
import itertools
import consts
from typing import Self, Optional, Any
from colorama import Fore
import fnmatch
from constraints import Constraint
from config import Config


@dataclass
class Task:
    id: int
    items: dict[str, Any]
    queue: "TaskQueue"

    @classmethod
    def new_task(cls, description: str, queue: "TaskQueue") -> Self:
        items: dict[str, Any] = {k: "" for k in queue.headers}
        pkid = (max(int(task.id) for task in queue.tasks) + 1) if queue.tasks else 1
        items[queue.header_pk()] = pkid
        items[queue.header_desc()] = description

        for k, v in items.items():
            constraint = queue.find_constraint_fallback(k)
            value = v

            if value == "":
                value = constraint.apply_default(value)

            value = constraint.constrain_variant(value)
            value = constraint.constrain_type(value)

            items[k] = value

        return cls(id=pkid, items=items, queue=queue)

    def update_column(self, k: str, v: str):
        km = self.queue.smart_header_match(k)
        if km is None:
            raise AssertionError("no existing column {k}")

        value = v
        constraint = self.queue.find_constraint_fallback(km)

        if value == "":
            value = constraint.apply_default(value)

        value = constraint.constrain_variant(value)
        value = constraint.constrain_type(value)
        self.items[km] = value

    def geti(self, header: str) -> Any:
        header_guess = self.queue.smart_header_match(header)
        assert header_guess and header_guess in self.items, f"column match failed for {header}"
        return self.items[header_guess]

    def seti(self, header: str, value: Any):
        header_guess = self.queue.smart_header_match(header)
        assert header_guess and header_guess in self.items, f"column match for {header}"
        self.items[header_guess] = value

    def matchi(self, header: str, cmp: str) -> bool:
        header_guess = self.queue.smart_header_match(header)
        assert header_guess and header_guess in self.items, f"column match for {header}"

        constraint = self.queue.find_constraint_fallback(header_guess)
        item = self.geti(header_guess)

        if constraint.Variant:
            cmp = constraint.constrain_variant(cmp)

        if fnmatch.fnmatch(item.lower(), cmp.lower()):
            return True

        return False

    @staticmethod
    def _get_pk(header: str, items: dict[str, Any]) -> int:
        pk = items.get(header)
        assert pk, f"fatal: PrimaryKey could not be found for Task {items}"
        try:
            return int(pk)
        except ValueError:
            raise AssertionError(f"fatal: PrimaryKey for Task {items} is not numeric")

    @classmethod
    def deserialize(cls, row: list[Any], headers: list[str], queue: "TaskQueue") -> Self:
        zipped = {k: v for k, v in zip(headers, row)}
        return cls(cls._get_pk(queue.header_pk(), zipped), zipped, queue)

    def to_display_row(self, headers: Optional[list[str]] = None) -> list[str]:
        headers = self.queue.get_display_headers() if headers is None else headers
        row = []
        for k in headers:
            constraint = self.queue.find_constraint_fallback(k)
            item = self.geti(k)
            item = item[: constraint.ColWidth] if constraint.ColWidth else item
            item = constraint.apply_colour(item)
            row.append(item)

        return row

    def serialize(self) -> list[Any]:
        return [self.items.get(k) for k in self.queue.headers]

    def is_archived(self) -> bool:
        constraint = self.queue.find_constraint("Role", "Archiving")
        if not constraint:
            return False

        value = self.items[self.queue.header_archive()]
        return constraint.constrain_type(value)


@dataclass
class TaskQueue:
    constraints: dict[str, Constraint]
    tasks: list[Task]
    headers: list[str]
    config: Config

    @classmethod
    def default(cls) -> Self:
        headers = list(consts.DEFAULT_HEADERS)
        constraint_list = [
            Constraint.kwargs(
                HeaderName="Id",
                Colours="*=BLUE",
                Role="PrimaryKey",
                Type="int",
            ),
            Constraint.kwargs(
                HeaderName="Archived",
                Role="Archiving",
                Type="bool",
                Colours="*=RED",
                Default="False",
            ),
            Constraint.kwargs(
                HeaderName="Priority",
                Colours="high=RED|medium=YELLOW|low=BLUE",
                Variant="High|Medium|Low",
                Default="Low",
            ),
            Constraint.kwargs(
                HeaderName="Status",
                Variant="Not Started|In Progress|Done",
                Colours="not started=GREY|in progress=YELLOW|done=GREEN",
                Role="Status",
                Default="Not Started",
            ),
            Constraint.kwargs(HeaderName="Task", Role="Description"),
            Constraint.kwargs(HeaderName="Assignee"),
        ]

        constraints = {c.HeaderName: c for c in constraint_list}
        return cls(
            constraints=constraints, headers=headers, tasks=[], config=Config.empty()
        )

    @classmethod
    def from_headers(cls, headers: list[str]) -> Self:
        constraints = {k: Constraint.empty(k) for k in headers}
        tq = cls(
            constraints=constraints, headers=headers, tasks=[], config=Config.empty()
        )
        return tq

    def add_task(self, task: Task) -> Task:
        self.tasks.append(task)
        return task

    def add_constraint(self, constraint: Constraint) -> Constraint:
        self.constraints[constraint.HeaderName] = constraint
        return constraint

    def find(self, id: int) -> Optional[Task]:
        return next((task for task in self.tasks if int(task.id) == id), None)

    def find_or_fail(self, id: int) -> Task:
        task = self.find(id)
        if not task:
            raise AssertionError(f"could not find task with id {id}")
        return task

    def find_constraint(self, header: str, value: Optional[str] = None) -> Optional[Constraint]:
        if value is None:
            return self.constraints.get(header)

        return next(
            (c for c in self.constraints.values() if c.__dict__[header] == value), None
        )

    def find_constraint_or_fail(
        self, header: str, value: Optional[str] = None, msg=None
    ) -> Constraint:
        constraint = self.find_constraint(header, value)

        if msg is None and value is None:
            msg = f"could not find constraint associated with {header}, make sure it has been added"
        elif msg is None:
            msg = f"could not find constraint with {header} set to {value}, make sure it has been set"

        assert constraint is not None, msg
        return constraint

    def find_constraint_fallback(self, header: str, value: Optional[str] = None) -> Constraint:
        return self.find_constraint(header, value) or Constraint.empty(header)

    def remove_task(self, id: int) -> Optional[Task]:
        start_len = len(self.tasks)
        for idx, task in enumerate(self.tasks):
            if int(task.id) == id:
                t = self.tasks.pop(idx)
                assert len(self.tasks) != start_len
                return t
        return None

    def header_pk(self) -> str:
        return self.find_constraint_or_fail(
            "Role",
            "PrimaryKey",
            "could not find PrimaryKey column, create it with 'tqb constraint alter [column] Role=PrimaryKey'",
        ).HeaderName

    def header_desc(self) -> str:
        query = self.find_constraint("Role", "Description")
        return (
            query.HeaderName
            if query is not None
            else next((h for h in self.headers if h != self.header_pk()))
        )

    def header_archive(self) -> str:
        return self.find_constraint_or_fail(
            "Role",
            "Archiving",
            "could not find Archiving column, create it with 'tqb constraint alter [column] Role=Archiving'",
        ).HeaderName

    def header_status(self) -> str:
        return self.find_constraint_or_fail(
            "Role",
            "Status",
            "could not find Status column, create it with 'tqb constraint alter [column] Role=Status'",
        ).HeaderName

    def get_display_headers(self) -> list[str]:
        return [h for h in self.headers if not self.find_constraint_fallback(h).Hide]

    def get_constraints_sorted_by_headers(self, headers: Optional[list[str]] = None) -> list[Constraint]:
        headers = headers or self.headers
        filtered_constraints = [
            c for c in self.constraints.values() if c.HeaderName in headers
        ]
        csorted = sorted(
            filtered_constraints, key=lambda x: headers.index(x.HeaderName)
        )
        return csorted

    def get_column_widths(self, headers: Optional[list[str]] = None) -> list[int | None]:
        return [
            c.ColWidth
            for c in self.get_constraints_sorted_by_headers(
                headers=headers or self.get_display_headers()
            )
        ]

    def smart_header_match(self, name: str) -> Optional[str]:
        for header in self.headers:
            if name.lower() == header.lower():
                return header
        return None
