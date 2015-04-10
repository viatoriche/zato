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

    def _get_item(self, items, name):
        for item in items:
            if item['name'] == name:
                return item

    def _add_file(self, name):
        f = open(name, 'w')
        f.write('{}={}'.format(*rand_string(2)))
        f.close()

    def _add_file_to_pickup_dir(self, name, pickup_dir, repo_location):
        if os.path.isabs(pickup_dir):
            self._add_file(os.path.join(pickup_dir, name))
        else:
            self._add_file(os.path.join(repo_location, pickup_dir, name))

    def test_get_list(self):

        repo_location = mkdtemp(prefix='repo_location')
        pickup_dir1 = mkdtemp(prefix='pickup_dir1')

        file_loc_dir1 = mkdtemp(prefix='file_loc_dir1')
        file_loc_dir2 = mkdtemp(prefix='file_loc_dir2')

        file1_name = os.path.join(file_loc_dir1, rand_string())
        file2_name = os.path.join(file_loc_dir2, rand_string())

        file3_no_fs_name = rand_string() # Note that it does not exist in file system

        # These two will be added to pickup dirs
        file4_name, file5_name = rand_string(2)

        try:

            # Relative to repo_location
            pickup_dir2 = 'ini'

            os.mkdir(os.path.join(repo_location, pickup_dir2))

            self._add_file(file1_name)
            self._add_file(file2_name)

            self._add_file_to_pickup_dir(file4_name, pickup_dir1, repo_location)
            self._add_file_to_pickup_dir(file5_name, pickup_dir2, repo_location)

            runtime_config = Bunch()
            runtime_config.pickup_dir = [pickup_dir1, pickup_dir2]
            runtime_config.file1_name = file1_name
            runtime_config.file2_name = file2_name
            runtime_config.file3_no_fs_name = file3_no_fs_name

            rcm = RuntimeConfigManager(_FakeServer(repo_location, runtime_config))
            items = rcm.get_items()

            self.assertEquals(len(items), 5)

            _file1 = self._get_item(items, 'file1_name')
            _file2 = self._get_item(items, 'file2_name')
            _file3_no_fs = self._get_item(items, 'file3_no_fs_name')
            _file4 = self._get_item(items, file4_name)
            _file5 = self._get_item(items, file5_name)

            self.assertEquals(_file1['pickup_dir'], None)
            self.assertEquals(_file1['name'], 'file1_name')
            self.assertEquals(_file1['full_path'], file1_name)
            self.assertEquals(_file1['access_rights'], '0664')

            self.assertEquals(_file2['pickup_dir'], None)
            self.assertEquals(_file2['name'], 'file2_name')
            self.assertEquals(_file2['full_path'], file2_name)
            self.assertEquals(_file2['access_rights'], '0664')

            self.assertEquals(_file3_no_fs['pickup_dir'], None)
            self.assertEquals(_file3_no_fs['name'], 'file3_no_fs_name')
            self.assertEquals(_file3_no_fs['full_path'], os.path.join(repo_location, file3_no_fs_name))
            self.assertEquals(_file3_no_fs['access_rights'], None) # It's None because the file doesn't really exist

            self.assertEquals(_file4['pickup_dir'], pickup_dir1)
            self.assertEquals(_file4['name'], file4_name)
            self.assertEquals(_file4['full_path'], os.path.join(repo_location, pickup_dir1, file4_name))
            self.assertEquals(_file4['access_rights'], '0664')

            self.assertEquals(_file5['pickup_dir'], pickup_dir2)
            self.assertEquals(_file5['name'], file5_name)
            self.assertEquals(_file5['full_path'], os.path.join(repo_location, pickup_dir2, file5_name))
            self.assertEquals(_file5['access_rights'], '0664')

        finally:
            rmtree(repo_location)
            rmtree(pickup_dir1)
            rmtree(file_loc_dir1)
            rmtree(file_loc_dir2)
