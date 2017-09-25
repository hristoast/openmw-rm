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
RES_DIR_NAMES = ["bookart", "fonts", "icons", "meshes", "music", "sound", "splash", "textures", "video"]
VERSION = "0.5"


# TODO: python and os check
# TODO: windows and macos support


def _get_version():
    # TODO: output based on git status
    pass


def get_terminal_dims() -> tuple:
    tty = os.popen('stty size', 'r')
    try:
        y, x = tty.read().split()
    except ValueError:
        y, x = ["0", "0"]
    tty.close()
    return x, y


def emit_log(msg: str, level=logging.INFO, quiet=False, verbose=False, *args, **kwargs) -> None:
    """Logging wrapper."""
    if not quiet:
        if not verbose and int(get_terminal_dims()[0]) > 0:
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
    """Call sys.ext(1) with a formatted error message to stderr."""
    sys.stderr.write("ERROR: " + msg + " Exiting ..." + "\n")
    sys.exit(1)


def check_openmw_cfg_path(path: str) -> T[bool, SystemExit]:
    """Check if the given openmw.cfg path exists, exit 1 if not."""
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


def flatten_resource_load_list(checked_data_paths_list: list, v: bool) -> dict:
    """
    Traverse each data path, in order, checking for each asset that it adds.

    Return a list of each asset in use and the full path to the canonical file
    (the one in use when the game is loaded.)

    This is a nonexact approximation of how the actual OpenMW loading happens.
    Also, if a mod uses a plugin to load one texture instead of another, this
    program has no way of knowing about that and so "dupes" will be stored in
    that sense.

    TODO: implement this exactly as is done in OpenMW
    """
    def _store_asset(_dict, _res, _file_low, _file, _count):
        emit_log("Storing #{0}: {1}".format(_count,
                                            os.path.join(_res, _file)),
                 level=logging.DEBUG, verbose=v)
        _dict.update({_file_low: os.path.join(_res, _file)})

    resource_load_dict = {}

    for _path in checked_data_paths_list:
        for ls in os.listdir(_path):
            # Lower case so we can check against predefined names
            _ls = ls.lower()
            for _dir in RES_DIR_NAMES:
                # Is this a valid resource directory
                # path (e.g. meshes, textures)?
                if _ls == _dir:
                    _res_path = os.path.join(_path, ls)
                    # List out the valid resource directory
                    # TODO: support for recursive listing;
                    # TODO: right now we only go one deep!
                    for root, dirs, files in os.walk(_res_path):
                        for _f in files:
                            # We're going to store the file name in all
                            # lowercase, do this now so we can later check
                            # to see if the file has been stored.
                            _f_low = _f.lower()
                            _f_low_nosuffix = _f_low.split('.')[0]
                            res_dict_copy = resource_load_dict.copy()
                            emit_log("Examining #{0}: {1}".format(len(res_dict_copy.keys()) + 1,
                                                                  os.path.join(_res_path, _f)),
                                     level=logging.DEBUG, verbose=v)
                            if len(res_dict_copy.keys()) > 0:
                                key_match = False
                                for _k in res_dict_copy.keys():
                                    # Stick a period at the end to prevent false matches
                                    if _k.startswith(_f_low_nosuffix + '.'):
                                        key_match = True
                                        emit_log("Rejecting #{0} {1} as there is already an entry for it!".format(
                                            len(res_dict_copy.keys()) + 1,
                                            os.path.join(_res_path, _f)),
                                            level=logging.DEBUG, verbose=v)
                                        # We have a match, break out of this loop
                                        break
                                    else:
                                        # No match, keep checking against keys
                                        continue
                                if not key_match:
                                    _store_asset(resource_load_dict, _res_path, _f_low, _f, len(res_dict_copy.keys()) + 1)
                            else:
                                _store_asset(resource_load_dict, _res_path, _f_low, _f, 1)

    return resource_load_dict


def read_openmw_cfg(cfg_path: str, verbose) -> tuple:
    """
    Read the given openmw.cfg file and perform checks and verifications on it.

    TODO: emit flattened asset lists and etc here too?
    TODO: how does mlox know how to sort plugins?
    TODO: and can it be done here, too?
    """
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
    return data_paths, content


def parse_args(args: list) -> None:
    flat_data = None
    force = False
    openmw_cfg = DEFAULT_CFG_FILE
    verbose = False
    parser = argparse.ArgumentParser(description=DESCRIPTION, prog=PROGNAME)
    actions = parser.add_argument_group("Actions")
    actions.add_argument("-F", "--flatten", action="store_true",
                         help="Generate a flattened resource list.")
    actions.add_argument("-s", "--scan", action="store_true",
                         help="Run a load order scan.")
    options = parser.add_argument_group("Options")
    options.add_argument("-f", "--file", dest='openmw_cfg', metavar="CFG FILE",
                         help="Specify the path to an openmw.cfg file.")
    options.add_argument("-v", "--verbose", action="store_true",
                         help="Show extra output.")
    options.add_argument("-W", "--write-file", dest='out_file',
                         metavar="OUT FILE",
                         help="Specify the path to an output file.")
    parser.add_argument("--version", action="version",
                        version=' '.join((PROGNAME, VERSION)),
                        help=argparse.SUPPRESS)
    parsed_args = parser.parse_args(args)

    if parsed_args.openmw_cfg:
        openmw_cfg = parsed_args.openmw_cfg
    if parsed_args.out_file:
        out_file = parsed_args.out_file
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

    # Read the cfg file and gather data
    data_paths, content = read_openmw_cfg(openmw_cfg, verbose)
    checked_data_paths = check_data_paths(data_paths)
    full_plugin_paths = get_content_paths(content, checked_data_paths)

    if parsed_args.scan or not parsed_args.flatten:
        # Do a normal scan by default or if specified alongside anything else
        emit_log("Running load order scan...")
        emit_log("Reading cfg file at: {}".format(os.path.abspath(openmw_cfg)))
        emit_log("Found {} data paths...".format(len(data_paths)))
        emit_log("Verified {} as existing.".format(len(checked_data_paths)))
        emit_log("Found {} activated plugins...".format(len(content)))
        emit_log("Verified {} full plugin paths.".format(len(full_plugin_paths)))
        emit_log("Current load order below:", level=logging.DEBUG, verbose=verbose)
        for num, p in full_plugin_paths.items():
            emit_log("{0}: {1}".format(str(num), p), level=logging.DEBUG,
                     verbose=verbose)

    # Do stuff with said data
    if parsed_args.flatten:
        emit_log("Generating flattened asset list (this will take several minutes)...")
        flat_data = flatten_resource_load_list(reversed(checked_data_paths), verbose)

        if out_file:
            with open(out_file, 'w') as f:
                for k, v in sorted(flat_data.items()):
                    f.write("{0}: {1}\n".format(k, v))
                f.close()
        else:
            emit_log("Asset loadout below:", level=logging.DEBUG)
            for k, v in sorted(flat_data.items()):
                emit_log("{0} Using: {1}".format(k, v), level=logging.DEBUG)

    emit_log("END {0} run at {1}".format(
        PROGNAME,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")), level=logging.DEBUG)


def main() -> None:
    try:
        parse_args(sys.argv[1:])
    except KeyboardInterrupt:
        error_and_die("Ctrl-C received!")


if __name__ == '__main__':
    main()
