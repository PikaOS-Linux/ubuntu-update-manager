#!/usr/bin/python3
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import os
import subprocess
import unittest

# pycodestyle is overdoing it a bit IMO
IGNORE_PYCODESTYLE = "E265,E402,W503"
IGNORE_FILES = ()


class TestPyCodeStyleClean(unittest.TestCase):
    """ensure that the tree is pycodestyle clean"""

    def test_pycodestyle_clean(self):
        CURDIR = os.path.dirname(os.path.abspath(__file__))
        py_files = set()
        for dirpath, dirs, files in os.walk(os.path.join(CURDIR, "..")):
            for f in files:
                if os.path.splitext(f)[1] != ".py":
                    continue
                    # islink to avoid running pycodestyle on imported files
                    # that are symlinks to other packages
                if os.path.islink(os.path.join(dirpath, f)):
                    continue
                if f in IGNORE_FILES:
                    continue
                py_files.add(os.path.join(dirpath, f))
        ret_code = subprocess.call(
            ["pycodestyle", "--ignore={0}".format(IGNORE_PYCODESTYLE)]
            + list(py_files)
        )
        self.assertEqual(0, ret_code)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
