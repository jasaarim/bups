import argparse
import logging
import textwrap
import time


logger = logging.getLogger(__name__)


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
    opts = parser.parse_args()

    return opts


COLORS = ['k', 'r', 'g', 'y', 'b', 'm', 'c', 'w']
COLOR_DICT = dict(zip(COLORS, range(30, 30 + len(COLORS))))


def _color_str(string, color):
    """Simple color formatter for logging formatter"""
    # For bold add 1; after "["
    start_seq = '\033[{:d}m'.format(COLOR_DICT[color])

    return start_seq + string + '\033[0m'


class BupsFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', width=70, indent=4,
                 font_effects=True):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.font_effects = font_effects
        self.wrapper = textwrap.TextWrapper(width=width,
                                            subsequent_indent=' '*indent)

    def format(self, record):

        if self.font_effects:
            if record.levelno >= 30:
                record.msg = _color_str(record.msg, 'r')
            elif hasattr(record, 'color'):
                record.msg = _color_str(record.msg, record.color)

        if hasattr(record, 'msg_only'):
            return '\n  ' + record.msg + '\n'

        if record.exc_info:
            output = super().format(record)
            output = textwrap.indent(output, ' '*3,
                                     lambda x: not x.startswith('E: ')
                                               and ' E: ' not in x)
            return output + '\n'
        else:
            record.msg = textwrap.dedent(record.msg)
            record.msg = record.msg.strip()
            output = self.wrapper.fill(super().format(record))
            if '\n' in output:
                output += '\n'
            return output


def configure_logging():
    fh = logging.FileHandler('backup.log')
    ch = logging.StreamHandler()

    minimal_formatter = BupsFormatter(fmt='%(levelname).1s: %(msg)s', indent=3)
    simple_formatter = BupsFormatter(fmt='%(asctime)s %(levelname).1s: %(msg)s',
                                     datefmt='%H:%M:%S', indent=12,
                                     font_effects=False)

    ch.setFormatter(minimal_formatter)
    fh.setFormatter(simple_formatter)
    logging.getLogger().addHandler(fh)
    logging.getLogger().addHandler(ch)
    logging.getLogger().setLevel(logging.INFO)


def main():
    opts = parse_opts()

    configure_logging()

    from .preparations import (InvalidFoldersException,
                               InvalidConfigException,
                               start_backup)

    try:
        logger.info('Starting back-up at {}'.format(time.strftime('%c')),
                    extra={'msg_only': 1, 'color': 'y'})
        start_backup(opts.source_root, opts.dest_root)
        logger.info('Back-up complete, congratulations! :)', extra={'msg_only': 1, 'color': 'y'})
    except InvalidFoldersException as exc:
        logger.error('Unable to make a back-up. ' + str(exc))
    except InvalidConfigException as exc:
        logger.error('Unable to read the configuration. ',exc_info=True)
    except KeyboardInterrupt:
        logger.info('Aborting execution, incomplete back-up')
    except Exception as exc:
        logger.error('Unknown error occurred. ', exc_info=True)
        logger.error('Incomplete back-up')
