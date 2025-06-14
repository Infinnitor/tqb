APP_NAME = "tqb"


DEFAULT_PATH = "taskqueue.csv"
DEFAULT_HEADERS = ("Id", "Task", "Assignee", "Status", "Priority", "Archived")
DEFAULT_SUBCOMMAND = "help"

CONSTRAINTS_BEGIN = "# BEGIN CONSTRAINTS"
CONSTRAINTS_HEADERS = ("HeaderName", "ConstrainType", "ConstrainVariant", "Default", "ColWidth", "Colours", "Role", "Autofill")
CONSTRAINTS_END = "# END CONSTRAINTS"
CONSTRAINT_ROLES = ("Status", "PrimaryKey", "Archiving", "Description")

HEADER_ID_STRING = "Id"

LS_TRUNCATE_LENGTH = 10
FALLBACK_TERMINAL_SIZE = 1000, 1000

STAR_MSG_OUTPUT_WIDTH = 80
STAR_CHARACTER_CHOICE = "-*★✦~"
