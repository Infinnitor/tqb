from tasks import TaskQueue, Task
from constraints import Constraint
from config import Config
from datetime import datetime
import consts


def default() -> TaskQueue:
    headers = list(consts.DEFAULT_HEADERS)
    constraint_list = [
        Constraint.kwargs(
            HeaderName="Id",
            Colours="*=BLUE",
            Role="PrimaryKey",
            Type="int",
        ),
        Constraint.kwargs(
            HeaderName="Task",
            Role="Description",
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
            Autofill=True,
        ),
        Constraint.kwargs(
            HeaderName="Status",
            Variant="Not Started|In Progress|Done",
            Colours="not started=GREY|in progress=YELLOW|done=GREEN",
            Role="Status",
            Default="Not Started",
            Autofill=True,
        ),
        Constraint.kwargs(HeaderName="Task", Role="Description"),
    ]

    constraints = {c.HeaderName: c for c in constraint_list}
    return TaskQueue(
        constraints=constraints, headers=headers, tasks=[], config=Config.empty()
    )


def todo() -> TaskQueue:
    headers = ["Id", "Task", "Done", "Archived"]
    constraint_list = [
        Constraint.kwargs(
            HeaderName="Id",
            Colours="*=BLUE",
            Role="PrimaryKey",
            Type="int",
        ),
        Constraint.kwargs(
            HeaderName="Task",
            Role="Description",
        ),
        Constraint.kwargs(
            HeaderName="Done",
            Variant="True|False",
            Colours="False=GREY|True=GREEN",
            Type="bool",
            Role="Status",
            Default="False",
            Autofill=True,
        ),
        Constraint.kwargs(
            HeaderName="Archived",
            Role="Archiving",
            Type="bool",
            Colours="*=RED",
            Default="False",
            Hide=True,
        ),
    ]

    constraints = {c.HeaderName: c for c in constraint_list}
    return TaskQueue(
        constraints=constraints, headers=headers, tasks=[], config=Config.empty()
    )


def development() -> TaskQueue:
    headers = ["Id", "Task", "Status", "Archived", "Complexity", "Area"]
    constraint_list = [
        Constraint.kwargs(
            HeaderName="Id",
            Colours="*=BLUE",
            Role="PrimaryKey",
            Type="int",
        ),
        Constraint.kwargs(
            HeaderName="Task",
            Colours="BUG:*=RED",
            Role="Description",
        ),
        Constraint.kwargs(
            HeaderName="Complexity",
            Colours="high=RED|medium=YELLOW|low=BLUE",
            Variant="High|Medium|Low",
            Default="Low",
            Autofill=True,
        ),
        Constraint.kwargs(
            HeaderName="Status",
            Variant="Not Started|In Progress|Done|Dependant|Backlog|Cancelled",
            Colours="not started=GREY|in progress=YELLOW|done=GREEN|Dependant=MAGENTA|Backlog=CYAN|Cancelled=BLUE",
            Role="Status",
            Default="Not Started",
            Autofill=True,
        ),
        Constraint.kwargs(
            HeaderName="Area",
            Colours="high=RED|medium=YELLOW|low=BLUE",
            Variant="Architecture|Feature|Bug Queue|Design|Management|Testing|Release",
            Default="",
            Autofill=True,
        ),
        Constraint.kwargs(
            HeaderName="Archived",
            Role="Archiving",
            Type="bool",
            Colours="*=RED",
            Default="False",
            Hide=True,
        ),
    ]

    constraints = {c.HeaderName: c for c in constraint_list}
    return TaskQueue(
        constraints=constraints, headers=headers, tasks=[], config=Config.empty()
    )


def sprint() -> TaskQueue:
    headers = ["Id", "Task", "Status", "Priority", "Area", "Sprint", "Year", "Archived"]
    MONTHS = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    sprints = []
    for month in MONTHS:
        sprints.append(f"H1 {month}")
        sprints.append(f"H2 {month}")

    constraint_list = [
        Constraint.kwargs(
            HeaderName="Id",
            Colours="*=BLUE",
            Role="PrimaryKey",
            Type="int",
        ),
        Constraint.kwargs(
            HeaderName="Task",
            Colours="BUG:*=RED",
            Role="Description",
        ),
        Constraint.kwargs(
            HeaderName="Status",
            Variant="Not Started|In Progress|Done|Dependant|Backlog|Cancelled",
            Colours="not started=GREY|in progress=YELLOW|done=GREEN|Dependant=MAGENTA|Backlog=CYAN|Cancelled=BLUE",
            Role="Status",
            Default="Not Started",
            Autofill=True,
        ),
        Constraint.kwargs(
            HeaderName="Priority",
            Colours="high=RED|medium=YELLOW|low=BLUE",
            Variant="High|Medium|Low",
            Default="Low",
            Autofill=True,
        ),
        Constraint.kwargs(
            HeaderName="Area",
            Variant="Architecture|Feature|Bug Queue|Design|Management|Testing|Release",
            Default="",
            Autofill=True,
        ),
        Constraint.kwargs(
            HeaderName="Sprint",
            Variant="|".join(sprints),
            Default="",
            Autofill=True,
        ),
        Constraint.kwargs(
            HeaderName="Year",
            Default=str(datetime.now().year),
        ),
        Constraint.kwargs(
            HeaderName="Archived",
            Role="Archiving",
            Type="bool",
            Colours="*=RED",
            Default="False",
            Hide=True,
        ),
    ]

    constraints = {c.HeaderName: c for c in constraint_list}
    return TaskQueue(
        constraints=constraints, headers=headers, tasks=[], config=Config.empty()
    )


def projects() -> TaskQueue:
    headers = ["Id", "Project", "Notes", "Archived"]
    constraint_list = [
        Constraint.kwargs(
            HeaderName="Id",
            Colours="*=BLUE",
            Role="PrimaryKey",
            Type="int",
        ),
        Constraint.kwargs(
            HeaderName="Project",
            Role="Description",
        ),
        Constraint.kwargs(
            HeaderName="Notes",
        ),
        Constraint.kwargs(
            HeaderName="Archived",
            Role="Archiving",
            Type="bool",
            Colours="*=RED",
            Default="False",
            Hide=True,
        ),
    ]

    constraints = {c.HeaderName: c for c in constraint_list}
    return TaskQueue(
        constraints=constraints, headers=headers, tasks=[], config=Config.empty()
    )


BLUEPRINT_MAP = {v.__name__: v for v in [default, todo, development, sprint, projects]}
__all__ = [v for v in BLUEPRINT_MAP.values()]
