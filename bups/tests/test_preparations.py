import tempfile
from nose.tools import ok_, assert_raises
from .. import preparations as prep
import os
from os.path import join

def test_make_and_check_ids():

    def check(_, source_root, dest_root, make_ids=True, raise_msg=None,
              force_dest=False):
        """Checking ids: {}"""
        def make_and_check():
            if make_ids:
                prep.make_ids(source_root, dest_root, force_dest)
            prep.check_ids(source_root, dest_root)
        if raise_msg is not None:
            with assert_raises(prep.InvalidFoldersException) as exc:
                make_and_check()
            ok_(raise_msg in str(exc.exception), raise_msg)
        else:
            make_and_check()


    with tempfile.TemporaryDirectory() as source_root, \
        tempfile.TemporaryDirectory() as dest_root:

        dest_id_file = join(dest_root, prep.ID_FILENAME)

        yield check, 'Empty directories', source_root, dest_root

        error_msg = 'Either source or destination is not a proper'
        yield check, 'Source and root mixed up', \
              dest_root, source_root, False, error_msg

        os.remove(dest_id_file)
        yield check, 'ID in source but not in destination', \
              source_root, dest_root

        with tempfile.TemporaryDirectory() as source_root2, \
                 tempfile.TemporaryDirectory() as dest_root2:
            prep.make_ids(source_root2, dest_root2)
            yield check, 'Invalid destination folder', \
                  source_root, dest_root2, False, \
                  'Are you sure you have the right directories?'

            yield check, 'Invalid source folder', \
                  source_root2, dest_root, False, \
                  'Are you sure you have the right directories?'

        with open(dest_id_file, 'ab') as f:
            f.write(b'\x01')
        yield check, 'Corrupted identifiers',\
              source_root, dest_root, False, \
              'At least one of the identifiers is invalid'

        os.remove(dest_id_file)
        yield check, 'An id file is missing', source_root, dest_root, \
              False, 'ID files do not exist in source or destination'

        open(join(dest_root, '.something'), 'w').close()
        yield check, 'Non-empty destination without forcing', source_root, \
              dest_root, True, 'Trying to couple a non-empty destination'

        with open(dest_id_file, 'w') as f:
            f.write('override this')
        yield check, 'Override destination with forcing', source_root, \
              dest_root, True, None, True


def test_writing_and_reading_config():

    def check(_, source_root, create_config=True, raise_msg=None):
        """Checking ids: {}"""
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
