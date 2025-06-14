from constraints import Constraint
from tasks import TaskQueue, Task
import csv
import itertools
import consts


def serialize(path: str, tq: TaskQueue):
    with open(path, "w+") as fp:
        writer = csv.writer(fp)
        writer.writerow([consts.CONSTRAINTS_BEGIN])
        writer.writerow(consts.CONSTRAINTS_HEADERS)

        for constraint in tq.constraints.values():
            writer.writerow(constraint.serialize())

        writer.writerow([consts.CONSTRAINTS_END])

        # Write the task headers for the tasks
        writer.writerow(tq.headers)

        for task in tq.tasks:
            writer.writerow(task.serialize())


def deserialize(path: str) -> TaskQueue:
    with open(path, "r", encoding="utf-8") as fp:
        reader = csv.reader(fp)
        list(itertools.takewhile(lambda x: x != [consts.CONSTRAINTS_BEGIN], reader))

        # Constraint headers
        _ = next(reader)

        constr_row = list(
            itertools.takewhile(lambda x: x != [consts.CONSTRAINTS_END], reader)
        )
        constraints = list(map(Constraint.deserialize, constr_row))
        c_dict = {c.HeaderName: c for c in constraints}
        headers = next(reader)

        tq = TaskQueue(c_dict, [], headers)
        for row in reader:
            if not row: continue
            task = Task.deserialize(row, headers, tq)
            tq.add_task(task)

    return tq
