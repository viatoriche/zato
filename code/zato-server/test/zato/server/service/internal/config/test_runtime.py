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

    def _run_test(self, assert_func):

        config = Bunch()

        config.repo_location = mkdtemp(prefix='repo_location')
        config.pickup_dir1 = mkdtemp(prefix='pickup_dir1')

        config.file_loc_dir1 = mkdtemp(prefix='file_loc_dir1')
        config.file_loc_dir2 = mkdtemp(prefix='file_loc_dir2')

        config.file1_name = os.path.join(config.file_loc_dir1, rand_string())
        config.file2_name = os.path.join(config.file_loc_dir2, rand_string())

        config.file3_no_fs_name = rand_string() # Note that it does not exist in file system

        # These two will be added to pickup dirs
        config.file4_name, config.file5_name = rand_string(2)

        try:

            # Relative to repo_location
            config.pickup_dir2 = 'ini'

            os.mkdir(os.path.join(config.repo_location, config.pickup_dir2))

            self._add_file(config.file1_name)
            self._add_file(config.file2_name)

            self._add_file_to_pickup_dir(config.file4_name, config.pickup_dir1, config.repo_location)
            self._add_file_to_pickup_dir(config.file5_name, config.pickup_dir2, config.repo_location)

            runtime_config = Bunch()
            runtime_config.pickup_dir = [config.pickup_dir1, config.pickup_dir2]
            runtime_config.file1_name = config.file1_name
            runtime_config.file2_name = config.file2_name
            runtime_config.file3_no_fs_name = config.file3_no_fs_name

            rcm = RuntimeConfigManager(_FakeServer(config.repo_location, runtime_config))
            config.items = rcm.get_items()

            self.assertEquals(len(config.items), 5)
            assert_func(rcm, config)

        finally:
            rmtree(config.repo_location)
            rmtree(config.pickup_dir1)
            rmtree(config.file_loc_dir1)
            rmtree(config.file_loc_dir2)

    def test_get_items(self):

        def assert_func(rcm, config):
            config._file1 = self._get_item(config.items, 'file1_name')
            config._file2 = self._get_item(config.items, 'file2_name')
            config._file3_no_fs = self._get_item(config.items, 'file3_no_fs_name')
            config._file4 = self._get_item(config.items, config.file4_name)
            config._file5 = self._get_item(config.items, config.file5_name)

            self.assertEquals(config._file1['pickup_dir'], None)
            self.assertEquals(config._file1['name'], 'file1_name')
            self.assertEquals(config._file1['full_path'], config.file1_name)
            self.assertEquals(config._file1['access_rights'], '0664')

            self.assertEquals(config._file2['pickup_dir'], None)
            self.assertEquals(config._file2['name'], 'file2_name')
            self.assertEquals(config._file2['full_path'], config.file2_name)
            self.assertEquals(config._file2['access_rights'], '0664')

            self.assertEquals(config._file3_no_fs['pickup_dir'], None)
            self.assertEquals(config._file3_no_fs['name'], 'file3_no_fs_name')
            self.assertEquals(config._file3_no_fs['full_path'], os.path.join(config.repo_location, config.file3_no_fs_name))
            self.assertEquals(config._file3_no_fs['access_rights'], None) # It's None because the file doesn't really exist

            self.assertEquals(config._file4['pickup_dir'], config.pickup_dir1)
            self.assertEquals(config._file4['name'], config.file4_name)
            self.assertEquals(config._file4['full_path'], os.path.join(config.repo_location, config.pickup_dir1, config.file4_name))
            self.assertEquals(config._file4['access_rights'], '0664')

            self.assertEquals(config._file5['pickup_dir'], config.pickup_dir2)
            self.assertEquals(config._file5['name'], config.file5_name)
            self.assertEquals(config._file5['full_path'], os.path.join(config.repo_location, config.pickup_dir2, config.file5_name))
            self.assertEquals(config._file5['access_rights'], '0664')

        self._run_test(assert_func)

    def test_edit(self):

        def assert_func(rcm, config):

            # Invalid source
            self.assertRaises(ValueError, rcm.edit, config.file4_name, config.pickup_dir1, rand_string())

            # No such pickup dir
            self.assertRaises(ValueError, rcm.edit, config.file4_name, rand_string(), '[zzz]\na=b')

            # No such file (but a valid pickup dir)
            self.assertRaises(ValueError, rcm.edit, rand_string(), config.pickup_dir1, '[zzz]\na=b')

            # All good
            valid_source = '[zzz]\na=b'
            rcm.edit(config.file4_name, config.pickup_dir1, valid_source)
            self.assertEquals(open(os.path.join(config.pickup_dir1, config.file4_name)).read(), valid_source)

        self._run_test(assert_func)

    def test_create(self):

        def assert_func(rcm, config):

            valid_source = '[zzz]\na=b'

            # No source
            self.assertRaises(ValueError, rcm.create, rand_string(), config.pickup_dir1, None)
            self.assertRaises(ValueError, rcm.create, rand_string(), config.pickup_dir1, '')

            # Unknown pickup dir
            self.assertRaises(ValueError, rcm.create, rand_string(), rand_string(), valid_source)

            # All good
            config_file_name = rand_string()
            rcm.create(config_file_name, config.pickup_dir1, valid_source)
            self.assertEquals(open(os.path.join(config.pickup_dir1, config_file_name)).read(), valid_source)

        self._run_test(assert_func)

    def test_validate(self):

        def assert_func(rcm, config):

            # No source
            result = rcm.validate('')
            self.assertFalse(result)
            self.assertEquals(result.details, 'Config file is empty')

            s = '[abc]\naa=bb\ncc=dd\ncc2=123\n[def]\nee=ff\ngg=hh\nzzz=\n[qwe]\naa={"a":"b","c":123,"d":2.0,"ee":{"ff":"gg"}}'

            result = rcm.validate(s)
            self.assertTrue(result)
            self.assertListEqual(result.config.keys(), ['abc', 'def', 'qwe'])
            self.assertDictEqual(result.config['abc'], {'aa': 'bb', 'cc': 'dd', 'cc2': 123})
            self.assertDictEqual(result.config['def'], {'ee': 'ff', 'gg': 'hh', 'zzz': ''})
            self.assertDictEqual(result.config['qwe'], {'aa': {'a': 'b', 'c': 123, 'd': 2.0, 'ee':{'ff':'gg'}}})

        self._run_test(assert_func)

    def test_get_source(self):

        def assert_func(rcm, config):

            # Good name, no pickup_dir
            source = rcm.get_source('file1_name')
            self.assertEquals(open(config.file1_name).read(), source)

            # Good name, good pickup_dir
            source = rcm.get_source(config.file4_name, config.pickup_dir1)
            self.assertEquals(open(os.path.join(config.pickup_dir1, config.file4_name)).read(), source)

            # Good name, incorrect pickup_dir
            self.assertRaises(ValueError, rcm.get_source, config.file4_name, rand_string())

            # Incorrect name, no pickup_dir
            self.assertRaises(ValueError, rcm.get_source, rand_string())

            # Incorrect name, good pickup_dir
            self.assertRaises(ValueError, rcm.get_source, rand_string(), config.pickup_dir1)

        self._run_test(assert_func)

    def test_get_full_path_exists(self):

        def assert_func(rcm, config):

            for name in ('get_full_path', 'exists'):

                func = getattr(rcm, name)

                # Good name, no pickup_dir
                self.assertTrue(func('file1_name'))

                # Good name, good pickup_dir
                self.assertTrue(func(config.file4_name, config.pickup_dir1))

                # Good name, incorrect pickup_dir
                self.assertRaises(ValueError, func, config.file4_name, rand_string())

                # Incorrect name, no pickup_dir
                self.assertRaises(ValueError, func, rand_string())

                # Incorrect name, good pickup_dir
                self.assertRaises(ValueError, func, rand_string(), config.pickup_dir1)

        self._run_test(assert_func)
