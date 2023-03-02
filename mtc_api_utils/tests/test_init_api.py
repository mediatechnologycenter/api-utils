#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

import os
import shutil
import unittest

from mtc_api_utils.init_api import download_if_not_exists, stem_tar_filename
from mtc_api_utils.tests.config import TestConfig

TEST_DOWNLOAD_DIR = "/tmp/test/download"


class TestInitApi(unittest.TestCase):
    def test_download_zip_file(self):
        remote_path = "https://polybox.ethz.ch/remote.php/dav/files/mtc_polybox/repo/tests/test_zip.tar.xz"
        stemmed_path = os.path.join(TEST_DOWNLOAD_DIR, stem_tar_filename(remote_path))

        if os.path.exists(stemmed_path):
            shutil.rmtree(stemmed_path)

        download_dir = download_if_not_exists(
            artifact_url=remote_path,
            download_dir=TEST_DOWNLOAD_DIR,
            polybox_auth=TestConfig.polybox_credentials,
            is_tar=True,
        )
        self.assertEqual(os.path.join(TEST_DOWNLOAD_DIR, "test_zip"), download_dir)
        self.assertTrue(os.path.isdir(download_dir), "Expected path to exist")
        self.assertTrue(os.path.isfile(os.path.join(stemmed_path, "test_image.jpg")), "Expected contained file to be in given location")

        shutil.rmtree(download_dir)

    def test_download_big_zip_file(self):
        self.skipTest("Skipped for time, re-enable when working on this package")

        remote_path = "https://polybox.ethz.ch/remote.php/dav/files/mtc_polybox/repo/tests/test-big-zip.tar.xz"
        stemmed_path = stem_tar_filename(remote_path)
        if os.path.exists(stemmed_path):
            shutil.rmtree(stemmed_path)
        download_dir = download_if_not_exists(
            artifact_url=remote_path,
            download_dir="TEST_DOWNLOAD_DIR",
            polybox_auth=TestConfig.polybox_credentials,
            is_tar=True,
        )
        self.assertEqual("test-big-zip", download_dir)
        self.assertTrue(os.path.isdir(download_dir))

        shutil.rmtree(download_dir)
