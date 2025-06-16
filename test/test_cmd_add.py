import os

RES_PATH = "test/res/"
TEST_PATH = "test/res/queue.csv"
PYTHON_PATH = "./venv/bin/python3"

os.makedirs(RES_PATH)


def test_cmd_create():
    os.system(f"{PYTHON_PATH} src/main.py --path {TEST_PATH} create")
    assert os.path.exists(TEST_PATH)

    os.remove(TEST_PATH)
