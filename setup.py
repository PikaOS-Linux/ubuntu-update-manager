#!/usr/bin/env python3
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import glob
import os
import pathlib
import re
from distutils.core import setup
from subprocess import check_output

from DistUtilsExtra.command import build_extra, build_help, build_i18n

disabled = []


def make_pep440_compliant(version: str) -> str:
    """Convert the version into a PEP440 compliant version."""
    if ":" in version:
        # Strip epoch
        version = version.split(":", 1)[1]
    public_version_re = re.compile(
        r"^([0-9][0-9.]*(?:(?:a|b|rc|.post|.dev)[0-9]+)*)\+?"
    )
    _, public, local = public_version_re.split(version, maxsplit=1)
    if not local:
        return version
    sanitized_local = re.sub("[+~]+", ".", local).strip(".")
    pep440_version = f"{public}+{sanitized_local}"
    assert re.match(
        "^[a-zA-Z0-9.]+$", sanitized_local
    ), f"'{pep440_version}' not PEP440 compliant"
    return pep440_version


def plugins():
    return []
    return [
        os.path.join("janitor/plugincore/plugins", name)
        for name in os.listdir("janitor/plugincore/plugins")
        if name.endswith("_plugin.py") and name not in disabled
    ]


for line in check_output(
    "dpkg-parsechangelog --format rfc822".split(), universal_newlines=True
).splitlines():
    header, colon, value = line.lower().partition(":")
    if header == "version":
        VERSION = make_pep440_compliant(value.strip())
        break
else:
    raise RuntimeError("No version found in debian/changelog")


class CustomBuild(build_extra.build_extra):
    def run(self):
        version_py = pathlib.Path("UpdateManager/UpdateManagerVersion.py")
        version_py.write_text(f"VERSION = '{VERSION}'\n", encoding="utf-8")
        build_extra.build_extra.run(self)


setup(
    name="update-manager",
    version=VERSION,
    packages=[
        "UpdateManager",
        "UpdateManager.backend",
        "UpdateManager.Core",
        "HweSupportStatus",
        "janitor",
        "janitor.plugincore",
    ],
    scripts=["update-manager", "ubuntu-security-status", "hwe-support-status"],
    data_files=[
        ("share/update-manager/gtkbuilder", glob.glob("data/gtkbuilder/*.ui")),
        ("share/man/man8", glob.glob("data/*.8")),
        ("share/GConf/gsettings/", ["data/update-manager.convert"]),
    ],
    cmdclass={
        "build": CustomBuild,
        "build_i18n": build_i18n.build_i18n,
        "build_help": build_help.build_help,
    },
)
