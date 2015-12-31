import yaml
import logging
import sys
from datetime import datetime
from os import mkdir, remove, listdir
from os.path import exists, join, basename, isdir, abspath, islink, realpath
from .backup_loop import make_backup, BackupNode


logger = logging.getLogger(__name__)

CONFIG_FILENAME = '.bups.config'

DEFAULT_EXCLUDES = ['.*', '*.pyc', '__pycache__']
DEFAULT_INCLUDES = ['.bash*', '.profile', '.emacs', '.vimrc', '.zsh*',
                    '.ssh', '.xsession', '.Xmodmap', '.xmonad', CONFIG_FILENAME]


class InvalidConfigException(ValueError):
    """If parsing configurations fails, this is raised"""
    pass


class InvalidFoldersException(ValueError):
    """Raised when there is something wrong with top-level folders"""
    pass


def start_backup(source_root, dest_root):
    source_root, dest_root = _make_absolute(source_root, dest_root)
    _validate_root_folders(source_root, dest_root)
    dest_root = _prepare_dest(source_root, dest_root)
    config = read_config(source_root)
    config_dest = read_config(dest_root)

    if config is None:
        if config_dest is None:
            config = prepare_first_backup(source_root, dest_root)
        else:
            msg = ('Destination has been used for back-up before but '
                   'seemingly for different source. Remove the config file '
                   'manually from the destination root if you want proceed.')
            raise InvalidFoldersException(msg)
    else:
        if config_dest is None:
            _maybe_force_dest(dest_root)
        elif config['id_string'] != config_dest['id_string']:
            msg = 'The config file in destination refers to another source.'
            raise InvalidFoldersException(msg)

    logger.info('Starting to make a back-up')
    make_backup(BackupNode(source_root, dest_root, '', config))


def _make_absolute(source_root, dest_root):
    if islink(source_root):
        logger.warning('Source is a link, changing to real path')
        source_root = realpath(source_root)

    if islink(dest_root):
        logger.warning('Destination is a link, changing to real path')
        dest_root = realpath(dest_root)

    return abspath(source_root), abspath(dest_root)


def _validate_root_folders(source_root, dest_root):
    error = None
    if not exists(source_root) or not exists(dest_root):
        error = 'Source or destination folder doesn\'t exist!'
    elif source_root.startswith(dest_root) or dest_root.startswith(source_root):
        error = 'Source or destination is contained by the other!'
    elif not isdir(dest_root):
        error = ('Destination contains an object of the same name as source, '
                 'but it is not a folder.')
    elif not isdir(source_root):
        error = 'Source must be a folder!'
    elif not is_writable(source_root):
        error = 'Source folder is not writable!'
    elif not is_writable(dest_root):
        error = 'Destination folder is not writable'

    if error is not None:
        raise InvalidFoldersException(error)


def _prepare_dest(source_root, dest_root):
    """Make sure that basenames are the same in source and dest"""
    source_base = basename(source_root)
    dest_base = basename(dest_root)

    if source_base == dest_base:
        return dest_root

    dest_root = join(dest_root, source_base)

    if exists(dest_root):
        if not isdir(dest_root):
            raise InvalidFoldersException('Destination contains an object of '
                                          'the same name as source, but it is '
                                          'not a folder.')
    else:
        logger.info('Creating folder {}'.format(dest_root))
        mkdir(dest_root)

    return dest_root


def is_writable(folder):
    test_file  = join(folder, 'bups_test_file_for_writing_permissions')
    try:
        open(test_file, 'w').close()
        return True
    except Exception:
        return False
    finally:
        if exists(test_file):
            remove(test_file)


def prepare_first_backup(source_root, dest_root):
    """Create configuration and identifies if they don't exist"""
    logger.info('Looks like this is the first using the source.',
                extra={'color':'g'})
    if listdir(dest_root):
        logger.warning('Destination is not empty. By proceeding '
                       'you risk overwriting the contents.')
        if not query_yes_no('Would you still like to proceed?'):
            raise InvalidFoldersException('Destination was not accepted.')

    config = create_default_config(source_root)

    return config


def _maybe_force_dest(dest_root):
    if listdir(dest_root):
        logger.warning('The destination folder does not contain a config file '
                       'that is in the source. If you proceed, you risk '
                       'overwriting files in destination.')
        if not query_yes_no('Would you still like to proceed?'):
            raise InvalidFoldersException('Destination was not accepted.')



def create_default_config(source_root):
    """Create a config which defines what is copied and what is not"""
    logger.info('Creating a default config file {} to source root'
                ''.format(CONFIG_FILENAME), extra={'color':'g'})
    config_file = join(source_root, CONFIG_FILENAME)

    id_string = source_root + datetime.now().strftime('  %Y-%m-%d %H:%M:%S.%f')

    config = dict(ignore_list=DEFAULT_EXCLUDES,
                  include_list=DEFAULT_INCLUDES,
                  id_string=id_string)

    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    return config


def read_config(directory):
    """Parse the configuration file from a directory"""
    config_file = join(directory, CONFIG_FILENAME)

    if not exists(config_file):
        return None

    with open(config_file, 'r') as f:
        config = yaml.load(f)
    validate_config(config)

    return config


def validate_config(config):
    """Check that the config contains correct fields"""
    if (not type(config) is dict or
        'include_list' not in config or
        'ignore_list' not in config or
        'id_string' not in config):
        raise InvalidConfigException('Invalid config file')


# This is roughly copied from http://code.activestate.com/recipes/577058-query-yesno/

def query_yes_no(question, default="no"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes":True, "y":True, "ye":True,
             "no":False, "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while 1:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid.keys():
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")