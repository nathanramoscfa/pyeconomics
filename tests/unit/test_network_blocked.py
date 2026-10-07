# tests/unit/test_network_blocked.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The suite runs with sockets disabled (pytest-socket's ``--disable-socket``).

A test that needs the network must opt in with ``@pytest.mark.enable_socket``;
none does in Phase 1. pytest-socket also warns as it raises, and the suite
turns warnings into errors, so a stray socket fails a test either way; these
tests record the warning to reach the SocketBlockedError behind it.
"""

from __future__ import annotations

import socket

import pytest
from pytest_socket import SocketBlockedError


def test_opening_a_socket_is_blocked() -> None:
    with (
        pytest.warns(UserWarning, match=r"socket\.socket"),
        pytest.raises(SocketBlockedError),
    ):
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def test_resolving_a_host_is_blocked() -> None:
    with (
        pytest.warns(UserWarning, match=r"socket\.getaddrinfo"),
        pytest.raises(SocketBlockedError),
    ):
        socket.create_connection(("192.0.2.1", 80), timeout=1)
