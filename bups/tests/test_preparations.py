import tempfile
from nose.tools import ok_, assert_raises
from mock import patch
from .. import preparations as prep
import shutil
from os.path import join
import unittest
import os


class SourceDestCouplingTestCase(unittest.TestCase):
    def setUp(self):
        self.dir1 = tempfile.TemporaryDirectory()
        self.dir2 = tempfile.TemporaryDirectory()
        self.source_root = join(self.dir1.name, 'folder')
        self.dest_root = join(self.dir2.name, 'folder')
        os.makedirs(self.source_root)
        os.makedirs(self.dest_root)

    def wrapDown(self):
        self.dir1.cleanup()
        self.dir2.cleanup()

    def test_config_in_both(self):
        """Start with the same config in source and dest"""
        prep.create_default_config(self.source_root)
        config_file = join(self.source_root, prep.CONFIG_FILENAME)
        shutil.copy(config_file, self.dest_root)
        prep.start_backup(self.source_root, self.dest_root)

    def test_different_config(self):
        """Start with different config in source and dest"""
        prep.create_default_config(self.source_root)
        prep.create_default_config(self.dest_root)
        with assert_raises(prep.InvalidFoldersException):
            prep.start_backup(self.source_root, self.dest_root)

    def test_config_in_dest(self):
        """Start with config only in destination"""
        prep.create_default_config(self.dest_root)
        with assert_raises(prep.InvalidFoldersException):
            prep.start_backup(self.source_root, self.dest_root)

    def test_config_in_source(self):
        """Start with config only in source and empty dest"""
        prep.create_default_config(self.source_root)
        prep.start_backup(self.source_root, self.dest_root)

    def test_config_in_source_non_empty_dest(self):
        """Start with config only in source and non-empty dest"""
        prep.create_default_config(self.source_root)
        dest_file = join(self.dest_root, 'file')
        with open(dest_file, 'w') as f:
            f.write('foo')
        with patch.object(prep, 'query_yes_no', return_value=False):
            with assert_raises(prep.InvalidFoldersException):
                prep.start_backup(self.source_root, self.dest_root)


def test_writing_and_reading_config():

    def check(_, source_root, create_config=True, raise_msg=None):
        """Check that the config file parses as expected"""
        if create_config:
            prep.create_default_config(source_root)
        if raise_msg is not None:
            with assert_raises(prep.InvalidConfigException) as exc:
                prep.read_config(source_root)
            ok_(raise_msg in str(exc.exception), raise_msg)
        else:
            configurations = prep.read_config(source_root)
            ok_(len(configurations['include_list']) > 0)
            ok_(len(configurations['ignore_list']) > 0)


    with tempfile.TemporaryDirectory() as source_root:

        config_file = join(source_root, prep.CONFIG_FILENAME)

        yield check, 'Empty directory', source_root

        open(config_file,'w').close()
        yield check, 'Empty config file', source_root, False, \
              'Invalid config file'

        yield check, 'Overwriting a config file', source_root
