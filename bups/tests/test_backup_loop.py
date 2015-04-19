import tempfile
import os
import unittest
from os.path import join, exists, isdir, isfile
from mock import patch
from nose.tools import ok_, eq_
from nose_parameterized import parameterized, param
from .. import backup_loop as bloop


def populate_dirs(source_root, dest_root):
    """Generate files and folders into two directories 

    """
    source_target = join(source_root, 'target')
    dir1 = join(source_target, 'dir1')
    dir2 = join(source_target, 'dir2')
    dir3 = join(source_target, 'dir3')
    dir_tricky = join(source_target, 'tricky directory@åäö')
    
    dest_target = join(dest_root, 'target')
    dir1_dest = join(dest_target,'dir1')
    dir4_dest = join(dest_target, 'dir4')
    
    os.makedirs(dir1)
    os.makedirs(dir2)
    os.makedirs(dir3)
    os.makedirs(dir1_dest)
    os.makedirs(dir4_dest)
    os.makedirs(dir_tricky)

    open(join(dest_target, 'file2'), 'w').close()
    open(join(dest_target, 'file3'), 'w').close()
    open(join(dest_target, 'file4'), 'w').close()
    open(join(dest_target, 'tricky file@äåö.'), 'w').close()
    # Make a file that has the same name as directory in source
    open(join(dest_target, 'dir3'), 'w').close()

    open(join(source_target, 'file1'), 'w').close()
    open(join(source_target, 'file2'), 'w').close()
    open(join(source_target, 'file3'), 'w').close()
    open(join(source_target, 'dir4'), 'w').close()
    open(join(source_target, 'tricky file@åäö.'), 'w').close()

    # Modification times so that the source is newer
    mtime = os.stat(join(dest_target, 'file2')).st_mtime
    os.utime(join(dest_target, 'file2'), (mtime-1e-5, mtime-1e-5))
    assert os.stat(join(dest_target, 'file2')).st_mtime < mtime
    mtime = os.stat(join(dest_target, 'dir4')).st_mtime
    os.utime(join(dest_target, 'dir4'), (mtime-1e-5, mtime-1e-5))
    assert os.stat(join(dest_target, 'dir4')).st_mtime < mtime

    # Modification time of file3 so that the target is newer
    mtime = os.stat(join(dest_target, 'file3')).st_mtime
    os.utime(join(dest_target, 'file3'), (mtime+1e-5, mtime+1e-5))
    assert os.stat(join(dest_target, 'file3')).st_mtime > mtime

    source_items = [join('target', i) for i in os.listdir(source_target)] 
    dest_items = [join('target', i) for i in os.listdir(dest_target)]
    
    return source_items, dest_items


@parameterized([
    param(populate_dirs),
])
def test_match_directories(populate_fun):

    new_targets = []
    archived = []

    def backup_call(source_root, dest_root, rel_path, config):
        new_targets.append(rel_path)

    def archive_call(root_path, rel_path):
        archived.append(join(root_path, rel_path))

    with tempfile.TemporaryDirectory() as source_root, \
            tempfile.TemporaryDirectory() as dest_root:
        source_items, dest_items =  populate_fun(source_root, dest_root)
        rel_path = 'target'
        with patch.object(bloop, 'make_backup', side_effect=backup_call), \
                patch.object(bloop, 'archive_item', side_effect=archive_call), \
                patch.object(bloop, 'check_include', return_value=True):
            bloop.match_directories(source_root, dest_root, rel_path, None)

        for item in source_items:
            ok_(item in new_targets)

        for item in dest_items:
            if item not in source_items:
                ok_(join(dest_root, item) in archived)
        

class MakeBackupTestCase(unittest.TestCase):

    def setUp(self):
        self.source_tempdir = tempfile.TemporaryDirectory()
        self.source_root = self.source_tempdir.name
        self.dest_tempdir = tempfile.TemporaryDirectory()
        self.dest_root = self.dest_tempdir.name
        populate_dirs(self.source_root, self.dest_root)

    def test_copy_new_directory(self):
        with patch.object(bloop, 'match_directories') as md:
            rel_path = join('target', 'dir2')
            target_folder = join(self.dest_root, rel_path)
            ok_(not exists(target_folder))
            bloop.make_backup(self.source_root, self.dest_root, rel_path, None)
            md.assert_called_once_with(self.source_root, self.dest_root,
                                       rel_path, None)
            ok_(exists(target_folder))
            ok_(isdir(target_folder))
            eq_(len(os.listdir(target_folder)), 0)

    def test_replace_file_with_directory(self):
        with patch.object(bloop, 'match_directories') as md:
            rel_path = join('target', 'dir3')
            target_folder = join(self.dest_root, rel_path)
            ok_(exists(target_folder))
            ok_(isfile(target_folder))
            bloop.make_backup(self.source_root, self.dest_root, rel_path, None)
            md.assert_called_once_with(self.source_root, self.dest_root,
                                       rel_path, None)
            ok_(exists(target_folder))
            ok_(isdir(target_folder))
            eq_(len(os.listdir(target_folder)), 0)

    def test_copy_a_new_file(self):
        rel_path = join('target', 'file1')
        target_file = join(self.dest_root, rel_path)
        ok_(not exists(target_file))
        bloop.make_backup(self.source_root, self.dest_root, rel_path, None)
        ok_(exists(target_file))
        ok_(isfile(target_file))

    def test_replace_an_older_file(self):
        rel_path = join('target', 'file2')
        target_file = join(self.dest_root, rel_path)
        source_file = join(self.source_root, rel_path)
        ok_(exists(target_file))
        old_mtime = os.stat(target_file).st_mtime
        new_mtime = os.stat(source_file).st_mtime
        ok_(old_mtime < new_mtime, (old_mtime, new_mtime))
        bloop.make_backup(self.source_root, self.dest_root, rel_path, None)
        ok_(exists(target_file))
        ok_(isfile(target_file))
        ok_(os.stat(target_file).st_mtime >= new_mtime)

    def test_replace_a_folder_with_file(self):
        rel_path = join('target', 'dir4')
        target_file = join(self.dest_root, rel_path)
        ok_(isdir(target_file))
        bloop.make_backup(self.source_root, self.dest_root, rel_path, None)
        ok_(exists(target_file))
        ok_(isfile(target_file))

    def test_file_with_tricky_characters(self):
        rel_path = join('target', 'tricky file@åäö.')
        target_file = join(self.dest_root, rel_path)
        ok_(not exists(target_file))
        bloop.make_backup(self.source_root, self.dest_root, rel_path, None)
        ok_(exists(target_file))
        ok_(isfile(target_file))

    def test_a_folder_with_tricky_characters(self):
        with patch.object(bloop, 'match_directories') as md:
            rel_path = join('target', 'tricky directory@åäö')
            target_folder = join(self.dest_root, rel_path)
            ok_(not exists(target_folder))
            bloop.make_backup(self.source_root, self.dest_root, rel_path, None)
            md.assert_called_once_with(self.source_root, self.dest_root,
                                       rel_path, None)
            ok_(exists(target_folder))
            ok_(isdir(target_folder))
            eq_(len(os.listdir(target_folder)), 0)

    def wrapDown(self):
        self.source_tempdir.cleanup()
        self.dest_tempdir.cleanup()

