#!/usr/bin/python3
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import logging
import mock
import sys
import unittest

from UpdateManager.Core import utils


class TestUtils(unittest.TestCase):
    def test_humanize_size(self):
        # humanize size is a bit funny, it rounds up to kB as the meaningful
        # unit for users
        self.assertEqual(utils.humanize_size(1000), "1 kB")
        self.assertEqual(utils.humanize_size(10), "1 kB")
        self.assertEqual(utils.humanize_size(1200), "2 kB")
        # but not for MB as well
        self.assertEqual(utils.humanize_size(1200 * 1000), "1.2 MB")
        self.assertEqual(utils.humanize_size(1478 * 1000), "1.5 MB")
        # and we don't go to Gb  just yet (as its not really needed
        # in a upgrade context most of the time
        self.assertEqual(utils.humanize_size(1000 * 1000 * 1000), "1000.0 MB")

    def test_is_child_of_process_name(self):
        data = "1 (systemd) S 0 1 1 0 -1 4194560 255183 71659081 87 18403 \
816 737 430168 107409 20 0 1 0 2 218931200 1882 18446744073709551615 1 1 0 0 \
0 0 671173123 4096 1260 0 0 0 17 3 0 0 469245113 0 258124 0 0 0 0 0 0 0 0"
        with mock.patch(
            "builtins.open", mock.mock_open(read_data=data)
        ) as mock_file:
            assert open("/proc/1/stat").read() == data
            mock_file.assert_called_with("/proc/1/stat")
            self.assertTrue(
                utils.is_child_of_process_name("init")
                or utils.is_child_of_process_name("systemd")
            )
            self.assertFalse(utils.is_child_of_process_name("mvo"))

    def test_is_port_listening(self):
        from UpdateManager.Core.utils import is_port_already_listening

        data = "9: 00000000:0016 00000000:0000 0A 00000000:00000000 \
00:00000000 00000000     0        0 11366514 1 0000000000000000 100 \
0 0 10 0"
        with mock.patch(
            "builtins.open", mock.mock_open(read_data=data)
        ) as mock_file:
            assert open("/proc/net/tcp").readlines() == [data]
            mock_file.assert_called_with("/proc/net/tcp")
            self.assertTrue(is_port_already_listening(22))

    def test_strip_auth_from_source_entry(self):
        from aptsources.sourceslist import SourceEntry

        # entry with PW
        s = SourceEntry("deb http://user:pass@some-ppa/ ubuntu main")
        self.assertTrue(
            "user" not in utils.get_string_with_no_auth_from_source_entry(s)
        )
        self.assertTrue(
            "pass" not in utils.get_string_with_no_auth_from_source_entry(s)
        )
        self.assertEqual(
            utils.get_string_with_no_auth_from_source_entry(s),
            "deb http://hidden-u:hidden-p@some-ppa/ ubuntu main",
        )
        # no pw
        s = SourceEntry("deb http://some-ppa/ ubuntu main")
        self.assertEqual(
            utils.get_string_with_no_auth_from_source_entry(s),
            "deb http://some-ppa/ ubuntu main",
        )

    @mock.patch("UpdateManager.Core.utils._load_meta_pkg_list")
    def test_flavor_package_ubuntu_first(self, mock_load):
        cache = {
            "ubuntu-desktop": mock.MagicMock(),
            "other-desktop": mock.MagicMock(),
        }
        cache["ubuntu-desktop"].is_installed = True
        cache["other-desktop"].is_installed = True
        mock_load.return_value = ["other-desktop"]
        self.assertEqual(
            utils.get_ubuntu_flavor_package(cache=cache), "ubuntu-desktop"
        )

    @mock.patch("UpdateManager.Core.utils._load_meta_pkg_list")
    def test_flavor_package_match(self, mock_load):
        cache = {
            "a": mock.MagicMock(),
            "b": mock.MagicMock(),
            "c": mock.MagicMock(),
        }
        cache["a"].is_installed = True
        cache["b"].is_installed = True
        cache["c"].is_installed = True
        mock_load.return_value = ["c", "a", "b"]
        # Must pick alphabetically first
        self.assertEqual(utils.get_ubuntu_flavor_package(cache=cache), "a")

    def test_flavor_package_default(self):
        self.assertEqual(
            utils.get_ubuntu_flavor_package(cache={}), "ubuntu-desktop"
        )

    def test_flavor_default(self):
        self.assertEqual(utils.get_ubuntu_flavor(cache={}), "ubuntu")

    @mock.patch("UpdateManager.Core.utils.get_ubuntu_flavor_package")
    def test_flavor_simple(self, mock_package):
        mock_package.return_value = "d"
        self.assertEqual(utils.get_ubuntu_flavor(), "d")

    @mock.patch("UpdateManager.Core.utils.get_ubuntu_flavor_package")
    def test_flavor_chop(self, mock_package):
        mock_package.return_value = "d-pkg"
        self.assertEqual(utils.get_ubuntu_flavor(), "d")

    @mock.patch("UpdateManager.Core.utils.get_ubuntu_flavor_package")
    def test_flavor_name_desktop(self, mock_package):
        mock_package.return_value = "something-desktop"
        self.assertEqual(utils.get_ubuntu_flavor_name(), "Something")

    @mock.patch("UpdateManager.Core.utils.get_ubuntu_flavor_package")
    def test_flavor_name_netbook(self, mock_package):
        mock_package.return_value = "something-netbook"
        self.assertEqual(utils.get_ubuntu_flavor_name(), "Something")

    @mock.patch("UpdateManager.Core.utils.get_ubuntu_flavor_package")
    def test_flavor_name_studio(self, mock_package):
        mock_package.return_value = "ubuntustudio-desktop"
        self.assertEqual(utils.get_ubuntu_flavor_name(), "Ubuntu Studio")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-v":
        logging.basicConfig(level=logging.DEBUG)
    unittest.main()
