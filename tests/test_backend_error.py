#!/usr/bin/python3
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import logging
import mock
import sys
import unittest
from mock import patch

import os

CURDIR = os.path.dirname(os.path.abspath(__file__))


class TestBackendError(unittest.TestCase):
    def setUp(self):
        os.environ["UPDATE_MANAGER_FORCE_BACKEND_APTDAEMON"] = "1"

        def clear_environ():
            del os.environ["UPDATE_MANAGER_FORCE_BACKEND_APTDAEMON"]

        self.addCleanup(clear_environ)

    @patch("UpdateManager.backend.InstallBackendAptdaemon.update")
    def test_backend_error(self, update):
        main = mock.MagicMock()
        main.datadir = os.path.join(CURDIR, "..", "data")

        from UpdateManager.backend import InstallBackend, get_backend

        update_backend = get_backend(main, InstallBackend.ACTION_UPDATE)
        update.side_effect = lambda: update_backend._action_done(
            InstallBackend.ACTION_UPDATE, True, False, "string", "desc"
        )
        update_backend.start()
        main.start_error.assert_called_once_with(True, "string", "desc")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-v":
        logging.basicConfig(level=logging.DEBUG)
    unittest.main()
