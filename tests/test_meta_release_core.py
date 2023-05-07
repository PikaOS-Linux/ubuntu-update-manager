#!/usr/bin/python3
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import distro_info
import glob
import logging
import multiprocessing
import os
import random
import sys
import tempfile
import time
import unittest

try:
    from test.support import EnvironmentVarGuard
except ImportError:
    from test.support.os_helper import EnvironmentVarGuard
from urllib.error import HTTPError
from urllib.request import install_opener, urlopen
from mock import patch
from http.server import BaseHTTPRequestHandler
from socketserver import TCPServer


from UpdateManager.Core.MetaRelease import (
    Dist,
    MetaReleaseCore,
    MetaReleaseParseError,
)
from UpdateManager.Core.utils import url_downloadable

CURDIR = os.path.dirname(os.path.abspath(__file__))


class SillyProxyRequestHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        code = 200
        info = ""
        try:
            f = urlopen(self.path)
            info = f.info()
        except HTTPError as e:
            code = e.code
        s = "HTTP/1.0 %s OK\n%s" % (code, info)
        self.wfile.write(s.encode("UTF-8"))

    # well, good enough
    do_GET = do_HEAD


def get_new_dist(current_release):
    """
    common code to test new dist fetching, get the new dist information
    for hardy+1
    """
    meta = MetaReleaseCore()
    # meta.DEBUG = True
    meta.current_dist_name = current_release
    fake_metarelease = os.path.join(CURDIR, "test-data", "meta-release")
    meta.METARELEASE_URI = "file://%s" % fake_metarelease
    while meta.downloading:
        time.sleep(0.1)
    meta._buildMetaReleaseFile()
    meta.download()
    return meta.new_dist


class TestMetaReleaseCore(unittest.TestCase):
    def setUp(self):
        self.new_dist = None
        self.port = random.randint(1025, 65535)
        self.httpd = TCPServer(("", self.port), SillyProxyRequestHandler)
        self.httpd_process = multiprocessing.Process(
            target=self.httpd.serve_forever
        )
        self.httpd_process.start()

    def tearDown(self):
        self.httpd_process.terminate()
        self.httpd_process.join()
        install_opener(None)

        bin_list = glob.glob(
            os.path.join(CURDIR, "aptroot-changelog/var/cache/apt/*.bin")
        )
        for bin_file in bin_list:
            try:
                os.remove(bin_file)
            except OSError:
                pass

    def testnewdist(self):
        """test that upgrades offer the right upgrade path"""
        for (current, next) in [
            ("dapper", "hardy"),
            ("hardy", "lucid"),
            ("intrepid", "jaunty"),
            ("jaunty", "karmic"),
            ("karmic", "lucid"),
        ]:
            new_dist = get_new_dist(current)
            self.assertEqual(
                next,
                new_dist.name,
                "New dist name for %s is '%s', "
                "but expected '%s''" % (current, new_dist.name, next),
            )

    @unittest.skipUnless(
        url_downloadable("https://ubuntu.com", logging.debug),
        "Could not reach https test site",
    )
    def test_https_url_downloadable(self):
        with EnvironmentVarGuard() as environ:
            logging.debug("no proxy, https address")
            del environ["http_proxy"]
            install_opener(None)
            self.assertTrue(
                url_downloadable("https://ubuntu.com", logging.debug),
                "download https with no proxy failed",
            )

    def test_url_downloadable(self):
        from UpdateManager.Core.utils import url_downloadable

        with EnvironmentVarGuard() as environ:
            # ensure that $no_proxy doesn't prevent us from accessing
            # localhost through proxy
            try:
                del environ["no_proxy"]
            except KeyError:
                pass
            logging.debug("proxy 1")
            environ["http_proxy"] = "http://localhost:%s/" % self.port
            install_opener(None)
            self.assertTrue(
                url_downloadable("http://archive.ubuntu.com", logging.debug),
                "download with proxy %s failed" % environ["http_proxy"],
            )
            logging.debug("proxy 2")
            environ["http_proxy"] = "http://localhost:%s" % self.port
            install_opener(None)
            self.assertTrue(
                url_downloadable("http://archive.ubuntu.com", logging.debug),
                "download with proxy %s failed" % environ["http_proxy"],
            )
            logging.debug("no proxy")
            del environ["http_proxy"]
            install_opener(None)
            self.assertTrue(
                url_downloadable("http://archive.ubuntu.com", logging.debug),
                "download with no proxy failed",
            )

            logging.debug("no proxy, no valid address")
            self.assertFalse(
                url_downloadable(
                    "http://archive.ubuntu.com/xxx", logging.debug
                ),
                "download with no proxy failed",
            )

            logging.debug("proxy, no valid address")
            environ["http_proxy"] = "http://localhost:%s" % self.port
            install_opener(None)
            self.assertFalse(
                url_downloadable(
                    "http://archive.ubuntu.com/xxx", logging.debug
                ),
                "download with no proxy failed",
            )

    def test_get_uri_query_string(self):
        # test with fake data, use a space to test quoting
        d = Dist("xenial", "16.04 LTS", "2016-04-21", True)
        meta = MetaReleaseCore()
        q = meta._get_release_notes_uri_query_string(d)
        self.assertTrue("os%3Dubuntu" in q)
        self.assertTrue("ver%3D16.04%20LTS" in q)

    def test_html_uri_real(self):
        # test parsing of a meta-releaes file from the server
        di = distro_info.UbuntuDistroInfo()
        ltses = [
            supported for supported in di.supported() if di.is_lts(supported)
        ]
        with EnvironmentVarGuard() as environ:
            environ["META_RELEASE_FAKE_CODENAME"] = ltses[-2]
            meta = MetaReleaseCore(forceDownload=True)
            while meta.downloading:
                time.sleep(0.1)
            # it's possible the next LTS is in development
            if meta.new_dist is None:
                meta = MetaReleaseCore(
                    useDevelopmentRelease=True, forceDownload=True
                )
                while meta.downloading:
                    time.sleep(0.1)
            self.assertIsNotNone(meta.new_dist)
            uri = meta.new_dist.releaseNotesHtmlUri
            f = urlopen(uri)
            data = f.read().decode("UTF-8")
            self.assertTrue(len(data) > 0)
            self.assertTrue("<html>" in data)

    @patch("UpdateManager.Core.MetaRelease.MetaReleaseCore.download")
    @patch(
        "UpdateManager.Core.MetaRelease.distro_info.UbuntuDistroInfo.is_lts"
    )
    def test_prompt_lts_ignored_for_non_lts(self, mock_is_lts, mock_download):
        with tempfile.NamedTemporaryFile() as f:
            # for non-LTS, Prompt=lts should not change the METARELEASE_URI
            mock_is_lts.return_value = False
            f.write(
                """
[DEFAULT]
Prompt=lts
""".encode(
                    "utf-8"
                )
            )
            f.flush()
            with patch.object(MetaReleaseCore, "CONF", f.name):
                meta = MetaReleaseCore()
            self.assertNotEqual(meta.METARELEASE_URI, meta.METARELEASE_URI_LTS)

    @patch("UpdateManager.Core.MetaRelease.MetaReleaseCore.download")
    def test_parse_fails_for_all_non_tagfiles(self, mock_download):
        meta = MetaReleaseCore()
        with tempfile.TemporaryFile() as f:
            f.write("random stuff".encode("utf-8"))
            f.seek(0)
            meta.metarelease_information = f
            self.assertRaises(MetaReleaseParseError, meta.parse)

    @patch("UpdateManager.Core.MetaRelease.MetaReleaseCore.download")
    def test_parse_good(self, mock_download):
        meta = MetaReleaseCore()
        meta.current_dist_name = "foo"
        with tempfile.TemporaryFile() as f:
            f.write(
                """Dist: foo
Supported: 1
Date: Thu, 26 Oct 2006 12:00:00 UTC
Version: 1.0

Dist: goo
Supported: 1
Date: Thu, 26 Oct 2016 12:00:00 UTC
Version: 2.0
            """.encode(
                    "utf-8"
                )
            )
            f.seek(0)
            meta.metarelease_information = f
            meta.parse()
            self.assertEqual(meta.upgradable_to.name, "goo")
            self.assertEqual(meta.upgradable_to.version, "2.0")
            self.assertEqual(meta.upgradable_to.supported, True)

    @patch("UpdateManager.Core.MetaRelease.MetaReleaseCore.download")
    def test_parse_next_release_unsupported(self, mock_download):
        # We should jump over an unsupported release. LP: #1497024
        meta = MetaReleaseCore()
        meta.current_dist_name = "foo"
        with tempfile.TemporaryFile() as f:
            f.write(
                """Dist: foo
Supported: 1
Date: Thu, 26 Oct 2006 12:00:00 UTC
Version: 1.0

Dist: goo
Supported: 0
Date: Thu, 26 Oct 2016 12:00:00 UTC
Version: 2.0

Dist: hoo
Supported: 1
Date: Thu, 26 Oct 2026 12:00:00 UTC
Version: 3.0
            """.encode(
                    "utf-8"
                )
            )
            f.seek(0)
            meta.metarelease_information = f
            meta.parse()
            self.assertEqual(meta.upgradable_to.name, "hoo")
            self.assertEqual(meta.upgradable_to.version, "3.0")
            self.assertEqual(meta.upgradable_to.supported, True)

    @patch("UpdateManager.Core.MetaRelease.MetaReleaseCore.download")
    def test_parse_next_release_unsupported_devel(self, mock_download):
        # We should not jump over an unsupported release if we are running in
        # "devel" mode. LP: #1497024
        meta = MetaReleaseCore()
        meta.current_dist_name = "foo"
        meta.useDevelopmentRelease = True
        with tempfile.TemporaryFile() as f:
            f.write(
                """Dist: foo
Supported: 1
Date: Thu, 26 Oct 2006 12:00:00 UTC
Version: 1.0

Dist: goo
Supported: 0
Date: Thu, 26 Oct 2016 12:00:00 UTC
Version: 2.0
            """.encode(
                    "utf-8"
                )
            )
            f.seek(0)
            meta.metarelease_information = f
            meta.parse()
            self.assertEqual(meta.upgradable_to.name, "goo")
            self.assertEqual(meta.upgradable_to.version, "2.0")
            self.assertEqual(meta.upgradable_to.supported, False)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-v":
        logging.basicConfig(level=logging.DEBUG)
    unittest.main()
