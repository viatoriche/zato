# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import os
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase

# Bunch
from bunch import Bunch

# Zato
from zato.common.test import rand_string
from zato.server.service.internal.config.runtime import RuntimeConfigManager

class _FakeServer(object):
    def __init__(self, repo_location, runtime_config):
        self.repo_location = repo_location
        self.fs_server_config = Bunch(runtime_config=runtime_config)

class TestRuntimeConfigManager(TestCase):

    def test_get_list(self):

        repo_location = mkdtemp()
        pickup_dir1 = mkdtemp()

        file_loc_dir1 = mkdtemp()
        file_loc_dir2 = mkdtemp()

        file1 = os.path.join(file_loc_dir1, rand_string())
        file2 = os.path.join(file_loc_dir2, rand_string())

        file3 = rand_string() # Note that it does not exist in file system

        try:

            # Relative to repo_location
            pickup_dir2 = 'ini'

            runtime_config = Bunch()
            runtime_config.pickup_dir = [pickup_dir1, pickup_dir2]
            runtime_config.file1 = file1
            runtime_config.file2 = file2
            runtime_config.file3 = file3

            rcm = RuntimeConfigManager(_FakeServer(repo_location, runtime_config))
            rcm.get_list()

        finally:
            rmtree(repo_location)
            rmtree(pickup_dir1)
            rmtree(file_loc_dir1)
            rmtree(file_loc_dir2)
