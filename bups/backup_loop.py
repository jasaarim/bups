import os
import shutil
import logging
from os.path import join, exists, isdir, isfile


LOGGER = logging.getLogger(__name__)


def make_backup(source_root, dest_root, rel_path, config):
    """Copy relative path item from source directory to destination

    Relative path should be present in both ``source_root`` and
    ``dest_root``.

    There are two loops. The first one copies the contents of source
    directory to dest. The second removes the contents of dest that
    were not present in source anymore.


    If a directory is contained both in source and destination,
    this function calls another function which in turns calls this again
    for each item in the directory.
    
    """
    source_item = join(source_root, rel_path)
    dest_item = join(dest_root, rel_path)

    # Copy the directory
    if isdir(source_item):
        if not exists(dest_item) or not isdir(dest_item):
            # If we are replacing a file, remove the file first
            LOGGER.info('Creating folder\n  {}'.format(source_item))
            if exists(dest_item) and not isdir(dest_item):
                archive_item(dest_root, rel_path)
            create_folder(dest_item)
        match_directories(source_root, dest_root, rel_path, config)
    # Copy the file if its newer
    elif isfile(source_item):
        source_mod_t = os.stat(source_item).st_mtime
        if not exists(dest_item) or source_mod_t > os.stat(dest_item).st_mtime:
            if exists(dest_item) and isdir(dest_item):
                archive_item(dest_root, rel_path)
            copy_file(source_item, dest_item)
    else:
        LOGGER.warning('Skipping item\n  {}'.format(source_item))


def match_directories(source_root, dest_root, rel_path, config):
    """Make the existing directories, source and destination, to match.
    
    This function is part of a recursive loop in which another function
    always calls this when two directories with same basenames exist
    in source and destination.

    """
    dest_contents = os.listdir(join(dest_root, rel_path))
    try:
        source_contents = os.listdir(join(source_root, rel_path))
    except Exception:
        LOGGER.error('Cannot list the contents of folder\n  '
                     '{}'.format(join(source_root, rel_path)), exc_info=True)
        return
    
    source_contents = [i for i in source_contents if check_include(i, config)]
    dest_contents = [i for i in dest_contents if check_include(i, config)]
    # Copy new contents
    for source_item in source_contents:
        new_rel_path = join(rel_path, source_item)
        make_backup(source_root, dest_root, new_rel_path, config)
    # Remove obsolete contents
    for dest_item in dest_contents:
        if dest_item not in source_contents:
            archive_item(dest_root, join(rel_path, dest_item))     


def check_include(path, config):
    """Should an item be excluded from back-up?

    """
    basename = os.path.basename(path)
    for case in config['include_list']:
        if case.match(basename):
            return True
    for case in config['ignore_list']:
        if case.match(basename):
            return False
    return True


def archive_item(root_path, rel_path):
    """Remove a file or folder

    As the name implies, this could be modified so that the item
    will be archived somewhere.

    """
    item = join(root_path, rel_path)
    LOGGER.info('Removing\n  {}'.format(item))
    try:
        if os.path.isdir(item):
            shutil.rmtree(item)
        else:
            os.remove(item)
    except Exception as exc:
        LOGGER.error('Cannot remove\n  {}'.format(path), exc_info=True)


def copy_file(source_item, dest_item):
  LOGGER.info('Copying file\n  {} to\n  {}'.format(source_item, dest_item))
  try:
      shutil.copy(source_item, dest_item)
  except Exception as exc:
      LOGGER.error('Unable to copy\n  {}'.format(source_item), exc_info=True)


def create_folder(path):
    try:
        os.mkdir(path)
    except Exception as exc:
        LOGGER.error('Unable to create a folder\n  {}'.format(path),
                     exc_info=True)
