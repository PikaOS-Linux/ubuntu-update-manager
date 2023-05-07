#!/usr/bin/python3
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import unittest

import apt_pkg
import logging
import os
import sys

from UpdateManager.Core.utils import init_proxy


class TestInitProxy(unittest.TestCase):
    proxy = "http://10.0.2.2:3128"
    https_proxy = "https://10.0.2.2:3128"

    def setUp(self):
        try:
            del os.environ["http_proxy"]
            del os.environ["https_proxy"]
        except KeyError:
            pass
        apt_pkg.config.clear("Acquire::http::proxy")
        apt_pkg.config.clear("Acquire::https::proxy")

    def tearDown(self):
        self.setUp()

    def testinitproxyMixed(self):
        apt_pkg.config.set("Acquire::http::proxy", self.proxy)
        apt_pkg.config.set("Acquire::https::proxy", self.https_proxy)
        from gi.repository import Gio

        settings = Gio.Settings.new("com.ubuntu.update-manager")
        detected_proxy = init_proxy(settings)
        self.assertEqual(
            detected_proxy, {"http": self.proxy, "https": self.https_proxy}
        )

    def testinitproxyHttpOnly(self):
        apt_pkg.config.set("Acquire::http::proxy", self.proxy)
        from gi.repository import Gio

        settings = Gio.Settings.new("com.ubuntu.update-manager")
        detected_proxy = init_proxy(settings)
        self.assertEqual(
            detected_proxy, {"http": self.proxy, "https": self.proxy}
        )

    def testinitproxyHttpOnlyWithHttpsUri(self):
        apt_pkg.config.set("Acquire::http::proxy", self.https_proxy)
        from gi.repository import Gio

        settings = Gio.Settings.new("com.ubuntu.update-manager")
        detected_proxy = init_proxy(settings)
        self.assertEqual(
            detected_proxy,
            {"http": self.https_proxy, "https": self.https_proxy},
        )

    def testinitproxyHttpsOnly(self):
        apt_pkg.config.set("Acquire::https::proxy", self.https_proxy)
        from gi.repository import Gio

        settings = Gio.Settings.new("com.ubuntu.update-manager")
        detected_proxy = init_proxy(settings)
        self.assertEqual(detected_proxy, {"https": self.https_proxy})

    def testinitproxyNoProxy(self):
        from gi.repository import Gio

        settings = Gio.Settings.new("com.ubuntu.update-manager")
        detected_proxy = init_proxy(settings)
        self.assertEqual(detected_proxy, {})


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-v":
        logging.basicConfig(level=logging.DEBUG)
    unittest.main()
