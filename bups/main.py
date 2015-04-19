import argparse
import os
import logging
import logging.config


def here():
    return os.path.dirname(os.path.abspath(__file__))


def parse_opts():
    parser = argparse.ArgumentParser(
        description=('Create or update a back-up for a directory. '
                     'The two directories are coupled, i.e., identifiers '
                     'are placed into them to prevent unwanted copying to '
                     'wrong locations. A file is copied only if its '
                     'modification time is greater in source than in '
                     'destination.'))
    parser.add_argument('source_root', metavar='source', type=str,
                        help='Directory to be backed-up')
    parser.add_argument('dest_root', metavar='destination',
                        type=str,
                        help='Directory where the back-up will be located')
    parser.add_argument('-f', '--force-dest', dest='force_dest',
                        action='store_true', default=False,
                        help=('Force the destination folder. '
                              'May overwrite and remove files and folders.'))
    parser.add_argument('-g', '--configure-logging', metavar='log_config',
                        type=str, dest='log_config',
                        default=os.path.join(here(), 'logging.conf'),
                        help=('Path to an ini-file that configures logging. '
                              'The default configuration prints the '
                              'messages to the console and also appends '
                              'to a file "backup.log" in current working '
                              'directory.  See, e.g., https://docs.python.org/'
                              '3.4/library/logging.config.html for information '
                              'on the format of the file.'))
    opts = parser.parse_args()

    opts.source_root = os.path.abspath(opts.source_root)
    opts.dest_root = os.path.abspath(opts.dest_root)

    return opts


def main():
    opts = parse_opts()

    logging.config.fileConfig(opts.log_config)
    
    from .preparations import (InvalidFoldersException,
                               InvalidConfigException,
                               start_backup)

    logger = logging.getLogger(__name__)
    
    try:
        start_backup(opts.source_root, opts.dest_root, opts.force_dest)
        logger.info('Back-up complete!')
    except InvalidFoldersException as exc:
        logger.error('Unable to make a back-up.\n\n{}'.format(str(exc)))
    except InvalidConfigException as exc:
        logger.error('Unable to read the configuration\n\n{}.'.format(str(exc)))
    except KeyboardInterrupt:
        logger.info('Aborting execution, incomplete back-up')
    except Exception as exc:
        logger.error('Unknown error occurred.\n\n', exc_info=True)
        logger.error('Incomplete back-up.')
