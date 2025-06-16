import sys
import os
import shutil

SRCPATH = "/src/"
TEST_QUEUE_PATH = "test/res/queue.csv"
TEST_RES_PATH = "test/res/"


def setup_teardown(func):
    os.makedirs(TEST_RES_PATH, exist_ok=True)
    func()
    shutil.rmtree(TEST_RES_PATH)


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + SRCPATH)
