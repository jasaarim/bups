import fnmatch
import shutil
import logging
from os import stat, listdir, remove, mkdir
from os.path import join, exists, isdir, isfile, basename, sep


logger = logging.getLogger(__name__)

COPIED = []
ERRORS = []


class BackupNode(object):
    """Data structure controlling copying files and folders to destination"""
    def __init__(self, source_root, dest_root, item, config):
        """Store parameters for copying one file or directory

        ``item`` is a relative path that is present ``source_root``
        and is copied to ``dest_root`` if it is not there or if it is
        modified.

        """
        self.source_root = source_root
        self.dest_root = dest_root
        self.item = item
        self.config = config

    @property
    def source_item(self):
        return join(self.source_root, self.item)

    @property
    def dest_item(self):
        return join(self.dest_root, self.item)

    def join_item(self, item):
        new_item = join(self.item, item)
        return BackupNode(self.source_root, self.dest_root, new_item,
                         self.config)

    def modified_contents(self):
        """Is the item in source newer than in destination"""
        source_mod_t = stat(self.source_item).st_mtime
        if not exists(self.dest_item):
            return True
        elif source_mod_t > stat(self.dest_item).st_mtime:
            return True
        else:
            return False

    def copy(self):
        logger.info('Copy {}'.format(self))
        try:
            shutil.copy(self.source_item, self.dest_item)
            COPIED.append(self.item)
        except Exception:
            logger.error('Unable to copy', exc_info=True)
            ERRORS.append(self.item)

    def create_folder(self):
        logger.info('Make directory {}'.format(self))
        try:
            mkdir(self.dest_item)
        except Exception:
            logger.error('Cannot make directory', exc_info=True)
            ERRORS.append(self.item)

    def remove(self):
        """Remove a file or folder from back-up"""
        item = self.dest_item
        logger.info('Removing from back-up: {}'.format(self))
        try:
            if isdir(item):
                shutil.rmtree(item)
            else:
                remove(item)
        except Exception:
            logger.error('Cannot remove  {}'.format(self), exc_info=True)
            ERRORS.append(self.dest_item)

    def get_children(self):
        try:
            dest_contents = listdir(self.dest_item)
            source_contents = listdir(self.source_item)
        except Exception:
            logger.error('Problem in listing contents of {}'
                         ''.format(self), exc_info=True)
            return [], []

        source_contents = [i for i in source_contents if check_include(i, self.config)]
        dest_contents = [i for i in dest_contents if check_include(i, self.config)]
        return source_contents, dest_contents

    def __str__(self):
        return shorten_path(self.item)


def shorten_path(path, soft_limit=40, hard_limit=60):
    if len(path) <= soft_limit:
        return path
    else:
        parts = path.split(sep)
        first = parts[0]
        target_len = len(first) + 5
        n = 0
        while target_len < soft_limit:
            n -= 1
            target_len += len(parts[n])
        if target_len > hard_limit:
            item_len = hard_limit - soft_limit
            if len(parts[n]) > item_len:
                parts[n] = parts[n][:item_len] + '...'
            elif len(first) > item_len:
                first = first[:item_len] + '...'
        return join(first, '...', *parts[n:])


def make_backup(node):
    """Copy an item from source directory to destination

    Together with :func:`match_directories` this function makes a
    recursive loop that walks through the file system hierarchy above
    ``node.source_root`` and mirrors the same hierarchy above
    ``node.dest_root``.  This function copies files and encountering
    a directory it is passed to ``match_directories``.
    ``match_directories`` lists directory contents and passes them one
    by one to this functions.

    """
    _handle_directory(node) or _handle_file(node) or _handle_other(node)


def _handle_directory(node):
    """Step 1 in :func:`make_backup`"""
    if isdir(node.source_item):
        if not exists(node.dest_item) or not isdir(node.dest_item):
            # If we are replacing a file, remove the file first
            if exists(node.dest_item) and not isdir(node.dest_item):
                node.remove()
            node.create_folder()
        match_directories(node)
        return True
    return False


def _handle_file(node):
    """Step 2 in :func:`make_backup`"""
    if isfile(node.source_item):
        if node.modified_contents:
            if exists(node.dest_item) and not isfile(node.dest_item):
                node.remove()
            node.copy()
        return True
    return False


def _handle_other(node):
    """Step 3 in :func:`make_backup`"""
    logger.warning('Skipping item {}'.format(node))
    return True


def match_directories(node):
    """Make the existing directories, source and destination, to match.

    This function is part of a recursive loop in which another function
    always calls this when two directories with same basenames exist
    in source and destination.

    """
    source_contents, dest_contents = node.get_children()

    # Copy new contents
    for source_item in source_contents:
        make_backup(node.join_item(source_item))
    # Remove obsolete contents
    for dest_item in dest_contents:
        if dest_item not in source_contents:
            node.join_item(dest_item).remove()


def check_include(path, config):
    """Should an item be excluded from back-up?"""
    base = basename(path)
    for include_pattern in config['include_list']:
        if fnmatch.fnmatch(base, include_pattern):
            return True
    for exclude_pattern in config['ignore_list']:
        if fnmatch.fnmatch(base, exclude_pattern):
            return False
    return True
