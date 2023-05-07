#!/usr/bin/python3
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import logging
import sys
import unittest
from gettext import gettext as _
from mock import patch

from UpdateManager.Dialogs import NoUpdatesDialog
from UpdateManager.UpdateManager import UpdateManager
from UpdateManager.UpdatesAvailable import UpdatesAvailable

import os

CURDIR = os.path.dirname(os.path.abspath(__file__))


class TestUpdateManagerError(unittest.TestCase):
    def setUp(self):
        patcher = patch("UpdateManager.UpdateManager.UpdateManager")
        self.addCleanup(patcher.stop)
        self.manager = patcher.start()
        self.manager._check_meta_release.return_value = False
        self.manager.hwe_replacement_packages = None
        self.manager.datadir = os.path.join(CURDIR, "..", "data")

    def test_error_no_updates(self):
        p = UpdateManager._make_available_pane(
            self.manager, 0, error_occurred=True
        )
        self.assertIsInstance(p, NoUpdatesDialog)
        header_markup = "<span size='larger' weight='bold'>%s</span>"
        self.assertEqual(
            p.label_header.get_label(),
            header_markup % _("No software updates are available."),
        )

    def test_error_with_updates(self):
        p = UpdateManager._make_available_pane(
            self.manager, 1, error_occurred=True
        )
        self.assertIsInstance(p, UpdatesAvailable)
        self.assertEqual(
            p.custom_desc, _("Some software couldn’t be checked for updates.")
        )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-v":
        logging.basicConfig(level=logging.DEBUG)
    unittest.main()
