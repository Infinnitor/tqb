APP_NAME = "tqb"
APP_PRODUCTION = False
APP_VERSION = "0.9a"
APP_VERSION_STRING = f"{APP_NAME}-{APP_VERSION}-{'release' if APP_PRODUCTION else 'dev'}"

DEFAULT_PATH = "taskqueue.csv"
DEFAULT_HEADERS = ("Id", "Task", "Assignee", "Status", "Priority", "Archived")
DEFAULT_SUBCOMMAND = "help"

CONSTRAINTS_BEGIN = "# BEGIN CONSTRAINTS"
CONSTRAINTS_HEADERS = ("HeaderName", "ConstrainType", "ConstrainVariant", "Default", "ColWidth", "Colours", "Role", "Autofill", "Hide")
CONSTRAINTS_END = "# END CONSTRAINTS"
CONSTRAINT_ROLES = ("Status", "PrimaryKey", "Archiving", "Description")

CONFIG_BEGIN = "# BEGIN CONFIG"
CONFIG_HEADERS = ("Key", "Value", "Opt")
CONFIG_END = "# END CONFIG"

CONFIG_ALIAS_NAMESPACE = "Alias"

HEADER_ID_STRING = "Id"

LS_TRUNCATE_LENGTH = 10
FALLBACK_TERMINAL_SIZE = 1000, 1000

STAR_MSG_OUTPUT_WIDTH = 80
STAR_CHARACTER_CHOICE = "-*★✦~"
