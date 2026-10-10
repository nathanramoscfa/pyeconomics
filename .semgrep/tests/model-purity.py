# .semgrep/tests/model-purity.py
# Test cases for .semgrep/rules/model-purity.yaml (semgrep --test).
# Deliberately impure code: excluded from the bandit and semgrep hooks.
import datetime
import datetime as dt
import logging
import math
import os
import random
import socket
import subprocess
import time
import warnings
from datetime import date, datetime as clock

import numpy
import numpy as np


def files_and_console(path, text):
    # ruleid: model-purity
    open(path)
    # ruleid: model-purity
    with open(path, "w") as handle:
        handle.write(text)
    # ruleid: model-purity
    print(text)
    # ruleid: model-purity
    answer = input("value: ")
    # ruleid: model-purity
    warnings.warn("use pyeconomics.core.warn instead")
    # ruleid: model-purity
    warnings.warn_explicit("explicit", UserWarning, "file.py", 1)
    # ruleid: model-purity
    logging.info("a message")
    # ruleid: model-purity
    logging.getLogger("model")
    return answer


def the_clock():
    # ruleid: model-purity
    time.time()
    # ruleid: model-purity
    time.perf_counter()
    # ruleid: model-purity
    time.sleep(1)
    # ruleid: model-purity
    datetime.datetime.now()
    # ruleid: model-purity
    dt.datetime.now()
    # ruleid: model-purity
    clock.now()
    # ruleid: model-purity
    datetime.datetime.utcnow()
    # ruleid: model-purity
    datetime.datetime.today()
    # ruleid: model-purity
    datetime.date.today()
    # ruleid: model-purity
    date.today()


def randomness(seed):
    # ruleid: model-purity
    random.random()
    # ruleid: model-purity
    random.seed(seed)
    # ruleid: model-purity
    np.random.seed(seed)
    # ruleid: model-purity
    np.random.rand(3)
    # ruleid: model-purity
    numpy.random.normal(0.0, 1.0, 10)
    # ruleid: model-purity
    np.random.default_rng()
    # ruleid: model-purity
    np.random.default_rng(None)
    # ruleid: model-purity
    numpy.random.randint(0, 10)


def the_environment(command, host):
    # ruleid: model-purity
    os.environ["HOME"]
    # ruleid: model-purity
    os.environ.get("HOME")
    # ruleid: model-purity
    os.getenv("HOME")
    # ruleid: model-purity
    os.system(command)
    # ruleid: model-purity
    subprocess.run(command)
    # ruleid: model-purity
    subprocess.Popen(command)
    # ruleid: model-purity
    socket.socket()
    # ruleid: model-purity
    socket.create_connection((host, 80))


def pure(values, generator):
    # ok: model-purity
    total = math.fsum(values)
    # ok: model-purity
    mean = sum(values) / len(values)
    # ok: model-purity
    draws = generator.normal(0.0, 1.0, 10)
    # ok: model-purity
    seeded = np.random.default_rng(42)
    # ok: model-purity
    bit_generator = np.random.PCG64(42)
    # ok: model-purity
    stream = np.random.Generator(np.random.PCG64(7))
    # ok: model-purity
    array = np.asarray(values)
    # ok: model-purity
    created = datetime.date(2026, 1, 1)
    # ok: model-purity
    later = created + datetime.timedelta(days=30)
    # ok: model-purity
    name = str(values).strip()
    # ok: model-purity
    environ = {"environ": 1}
    # ok: model-purity
    timer = {"time": 1}["time"]
    return total, mean, draws, seeded, bit_generator, stream, array, later, name, environ, timer
