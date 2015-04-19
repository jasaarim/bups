import uuid
import json
import os
import re
import logging
from os.path import exists, join
from .backup_loop import make_backup


LOGGER = logging.getLogger(__name__)

CONFIG_FILENAME = '.backup.conf'
ID_FILENAME = '.backup.id'


class InvalidConfigException(ValueError):
    """If parsing configurations fails, this is raised

    """
    pass


class InvalidFoldersException(ValueError):
    """If top-level folders do not exists, raise this

    """
    pass


def start_backup(source_root, dest_root, force_dest):
    """When the back-up loop is entered, make initial configuration

    """
    if not exists(source_root) or not exists(dest_root) or \
            not os.access(source_root, os.W_OK) or \
            not os.access(dest_root, os.W_OK):
        raise InvalidFoldersException('Invalid root folders or cannot '
                                      'write into them!')

    LOGGER.info('Checking if identifiers match in source and destination.')
    try:
        check_ids(source_root, dest_root)
    except InvalidFoldersException:
        # This may still raise the same type of exception.
        # The exception should be caught by the caller.
        make_ids(source_root, dest_root, force_dest)
        check_ids(source_root, dest_root)

    LOGGER.info('Reading configuration file.')
    config = read_config(source_root)

    if config is None:
        LOGGER.info('No configuration file found in source.\n'
                    'Default configuration is created to text file'
                    '\n\n  {}.\n\n''Edit the file if you want to '
                    'change the defaults.\n'
                    ''.format(join(source_root, CONFIG_FILENAME)))
        create_default_config(source_root)
        config = read_config(source_root)
        assert config is not None

    LOGGER.info('Starting to make a back-up.')
    make_backup(source_root, dest_root, '', config)


def read_config(directory):
    """Parse the configuration file from a directory

    """
    config_file = join(directory, CONFIG_FILENAME)

    if not exists(config_file):
        return None

    with open(config_file, 'r') as f:
        try:
            config = json.load(f)
            config = process_raw_config(config)
        except Exception as exc:
            msg = ('Invalid config file in\n\n  {}\n\n'.format(config_file))
            raise InvalidConfigException(msg + str(exc))

    return config


def process_raw_config(config):
    """Convert the config fields into their final form

    """
    try:
        config['include_list'] = [re.compile(i) for i in config['include_list']]
        config['ignore_list'] = [re.compile(i) for i in config['ignore_list']]
    except Exception as exc:
        msg = ('Not proper include_list and ignore_list in config. '
               'Either a list is missing or elements cannot be compiled '
               'into regular expressions.\n\n')
        raise InvalidConfigException(msg + str(exc))
    
    return config


def create_default_config(source_root):
    """Create a config which defines what is copied and what is not

    """
    config_file = join(source_root, CONFIG_FILENAME)
    
    help_msg = ('Items in ignore_list and include_list are expected '
                'to be regural expression.')

    config = dict(ignore_list=['^\.'],
                  include_list=['^\.bash', '^\.emacs', '^\.xmonad',
                                '^\.xsession'],
                  description=help_msg)

    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    return config_file


def check_ids(source_root, dest_root):
    """Check that we aren't accidentally copying files into wrong location

    """
    id_file1 = join(source_root, ID_FILENAME)
    id_file2 = join(dest_root, ID_FILENAME)
    config_file = join(source_root, CONFIG_FILENAME)

    if not exists(id_file1) or not exists(id_file2):
        raise InvalidFoldersException('ID files do not exist in source ' 
                                      'or destination')

    with open(id_file1, 'rb') as f1, open(id_file2, 'rb') as f2:
        id1 = f1.read()
        id2 = f2.read()

    try:
        uuid1 = uuid.UUID(bytes=id1[1:])
        uuid2 = uuid.UUID(bytes=id2[1:])
    except ValueError as exc:
        raise InvalidFoldersException('At least one of the identifiers is '
                                      'invalid:\n\n  {}\n  {}\n'
                                      ''.format(id_file1, id_file2))

    msg = None
    if int(id1[0]) != 1 or int(id2[0]) != 255:
        msg = ('Either source or destination is not a proper source or '
               'destination according to their identifier files.')
    if uuid1 != uuid2:
        msg = ('Identifiers\n\n  {}\n\nand \n\n  {}\n\ndo not match.\n'
               'Are you sure you have the right directories?\n'
               'Any content in destination may be overwritten.\n'
               'If you wish to proceed, you have to remove the '
               'config file\n\n  {}\n\nand the identifiers are created '
               'again when you run the program next time.'
               ''.format(id_file1, id_file2, config_file))
    if msg is not None:
       raise InvalidFoldersException(msg) 


def make_ids(source_root, dest_root, force_dest=False):
    """Create identifier files 

    Write a random uuid to a file to both directories.  In source directory
    add a byte '\x01' to the beginning and in destination directory add
    '\xff' to the beginning.

    If the source already has an identifier, it is used to create the
    identifier in the destination folder.

    """
    id_file1 = join(source_root, ID_FILENAME)
    id_file2 = join(dest_root, ID_FILENAME)

    if not force_dest and len(os.listdir(dest_root)):
        msg = ('Trying to couple a non-empty destination directory\n\n'
               '  {}\n\nwith\n\n  {}.\n\n'.format(dest_root, source_root))
        raise InvalidFoldersException(msg)

    if exists(id_file1):
        with open(id_file1, 'rb') as f:
            bytes = f.read()
            if int(bytes[0]) != 1:
                raise ValueError('Invalid source identifier in {}'
                                 ''.format(id_file1))
            try:
                ident = uuid.UUID(bytes=bytes[1:]).bytes
            except ValueError as exc:
                raise ValueError('Corrupted identifier in {}: '
                                 ''.format(id_file1) + str(exc))
    else:
        ident = uuid.uuid4().bytes

    with open(id_file1, 'wb') as f1, \
           open(id_file2, 'wb') as f2:
        f1.write(b'\x01' + ident)
        f2.write(b'\xff' + ident)

