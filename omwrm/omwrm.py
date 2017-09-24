import argparse
import logging
import os
import sys
import textwrap

from datetime import datetime
from typing import Union as T


DEFAULT_CFG_FILE = os.path.join(os.getenv("HOME"), ".config", "openmw", "openmw.cfg")
DESCRIPTION = "OpenMW Resource Manager - reads an openmw.cfg file to produce resource load information."
LICENSE = 'GPLv3'
LOGFMT = '==> %(message)s'
PROGNAME = "openmw-rm"
RES_DIR_NAMES = ["BookArt", "Fonts", "Icons", "Meshes", "Music", "Sound", "Splash", "Textures", "Video"]
VERSION = "0.2"


def get_terminal_dims() -> tuple:
    tty = os.popen('stty size', 'r')
    y, x = tty.read().split()
    tty.close()
    return x, y


def emit_log(msg: str, level=logging.INFO, quiet=False, verbose=False, *args, **kwargs) -> None:  # TODO: verify this return type
    if not quiet:
        if not verbose:
            msg = textwrap.shorten(msg, width=int(get_terminal_dims()[0]) - 5,
                                   placeholder="...")
        if level == logging.DEBUG:
            logging.debug(msg, *args, **kwargs)
        elif level == logging.INFO:
            logging.info(msg, *args, **kwargs)
        elif level == logging.WARN:
            logging.warn(msg, *args, **kwargs)
        elif level == logging.ERROR:
            logging.error(msg, *args, **kwargs)


def error_and_die(msg: str) -> SystemExit:
    sys.stderr.write("ERROR: " + msg + " Exiting ..." + "\n")
    sys.exit(1)


def check_openmw_cfg_path(path: str) -> T[bool, SystemExit]:
    path_exists = os.path.isfile(path)
    if not path_exists:
        error_and_die("{} could not be found!".format(path))
    return True


def check_data_paths(data_paths: list) -> list:
    """Takes a list of data paths and returns a list of those that exist."""
    checked_paths = []
    for p in data_paths:
        path_string = p.split("data=")[-1].strip('"').rstrip('"\n')
        if os.path.isdir(path_string):
            checked_paths.append(path_string)
    return checked_paths


def get_content_paths(content_names: list, data_paths: list) -> list:
    """
    Checks for the full path of each content plugin and returns a list of
    each's full path if found.

    Takes two lists: the first a list of content names, the second a list of
    data paths which are expected to have been checked to exist already.
    """
    content_paths_with_order = {}
    order_pos = 0
    for n in content_names:
        name = n.split('content=')[-1].rstrip()
        for p in data_paths:
            proposed_path = os.path.join(p, name)
            if os.path.exists(proposed_path):
                order_pos += 1
                content_paths_with_order.update({order_pos: proposed_path})
    return content_paths_with_order


def flatten_resource_load_list(data_paths):
    # resource_load_dict = {}
    pass


def read_openmw_cfg(cfg_path: str, verbose) -> None:  # TODO: verify this return type
    content = []
    data_paths = []
    check_openmw_cfg_path(cfg_path)
    cfg = open(cfg_path)
    line_list = cfg.readlines()
    cfg.close()
    for line in line_list:
        if line.startswith('content='):
            content.append(line)
        elif line.startswith('data='):
            data_paths.append(line)
    emit_log("Found {} data paths...".format(len(data_paths)))
    checked_data_paths = check_data_paths(data_paths)
    emit_log("Verified {} as existing.".format(len(checked_data_paths)))
    emit_log("Found {} activated plugins...".format(len(content)))
    full_plugin_paths = get_content_paths(content, checked_data_paths)
    emit_log("Verified {} full plugin paths.".format(len(full_plugin_paths)))
    emit_log("Current load order below:", level=logging.DEBUG, verbose=verbose)
    for num, p in full_plugin_paths.items():
        emit_log("{0}: {1}".format(str(num), p), level=logging.DEBUG,
                 verbose=verbose)
    # TODO: check all asset paths and print out which are the last loaded
    # TODO: print out a sorted load order


def parse_args(args: list) -> None:  # TODO: verify this return type
    force = False
    openmw_cfg = DEFAULT_CFG_FILE
    verbose = False
    parser = argparse.ArgumentParser(description=DESCRIPTION, prog=PROGNAME)
    options = parser.add_argument_group("Options")
    options.add_argument("-f", "--file", dest='openmw_cfg', metavar="CFG FILE",
                         help="Specify the path to an openmw.cfg file.")
    options.add_argument("-v", "--verbose", action="store_true",
                         help="Show extra output.")
    parser.add_argument("--version", action="version",
                        version=' '.join((PROGNAME, VERSION)),
                        help=argparse.SUPPRESS)
    parsed_args = parser.parse_args(args)

    if parsed_args.openmw_cfg:
        openmw_cfg = parsed_args.openmw_cfg
    if parsed_args.verbose:
        verbose = True

    if verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(format=LOGFMT, level=log_level, stream=sys.stdout)

    emit_log("BEGIN {0} run at {1}".format(
        PROGNAME,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")), level=logging.DEBUG)

    emit_log("Force: {}".format(force), level=logging.DEBUG)
    emit_log("Verbose: {}".format(verbose), level=logging.DEBUG)
    emit_log("Reading cfg file at: {}".format(os.path.abspath(openmw_cfg)))
    read_openmw_cfg(openmw_cfg, verbose)

    emit_log("END {0} run at {1}".format(
        PROGNAME,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")), level=logging.DEBUG)


def main() -> None:  # TODO: verify this return type
    try:
        parse_args(sys.argv[1:])
    except KeyboardInterrupt:
        error_and_die("Ctrl-C received!")


if __name__ == '__main__':
    main()
