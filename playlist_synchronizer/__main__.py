import argparse
import logging


from playlist_synchronizer.diff import calculate_diff
from playlist_synchronizer.sync import sync_dirs
from playlist_synchronizer.importer import (
    import_cmus,
    import_m3u8,
)

log = logging.getLogger(__name__)


class ArgumentException(Exception):
    pass


def parse_playlist(file, format, prefix):
    if format == "m3u8":
        with open(file, "r") as fp:
            return import_m3u8(fp)
    elif format == "cmus":
        if prefix is None:
            raise ArgumentException(
                "prefix must be specified for file type cmus"
            )
        with open(file, "r") as fp:
            return import_cmus(prefix, fp)
    else:
        raise ArgumentException(f"Invalid format {format}")


def run_cmd_parse(args):
    playlist = parse_playlist(args.file, args.format, args.prefix)
    print("\n".join(list(map(str, playlist.tracks))))


def run_cmd_diff(args):
    playlist_left = parse_playlist(args.file_left, args.format_left, args.prefix_left)
    playlist_right = parse_playlist(args.file_right, args.format_right, args.prefix_right)
    diff = calculate_diff(playlist_left, playlist_right)
    print(diff)


def run_cmd_convert(args):
    playlist = parse_playlist(args.file_from, args.format_from, args.prefix_from)
    with open(args.file_to, "w") as file:
        if args.format_to == "m3u8":
            playlist.write_m3u8(file)
        elif args.format_to == "cmus":
            playlist.write_cmus(file, args.prefix_to)


def run_cmd_sync_dirs(args):
    log.info(
        "Synchronizing %s and %s (using %s as cache)",
        args.dir_cmus,
        args.dir_m3u8,
        args.dir_sync_cache,
    )
    sync_dirs(args.dir_cmus, args.dir_m3u8, args.dir_sync_cache, args.cmus_prefix)
    log.info("Synchronization complete.")


def parse_args():
    ap = argparse.ArgumentParser()
    cmd = ap.add_subparsers(required=True)

    cmd_parse = cmd.add_parser("parse")
    cmd_parse.add_argument("--format", required=True)
    cmd_parse.add_argument("--file", required=True)
    cmd_parse.add_argument("--prefix", default=None)
    cmd_parse.set_defaults(fn=run_cmd_parse)

    cmd_diff = cmd.add_parser("diff")
    cmd_diff.add_argument("--format_left", required=True)
    cmd_diff.add_argument("--file_left", required=True)
    cmd_diff.add_argument("--prefix_left", default=None)
    cmd_diff.add_argument("--format_right", required=True)
    cmd_diff.add_argument("--file_right", required=True)
    cmd_diff.add_argument("--prefix_right", default=None)
    cmd_diff.set_defaults(fn=run_cmd_diff)

    cmd_diff = cmd.add_parser("convert")
    cmd_diff.add_argument("--format_from", required=True)
    cmd_diff.add_argument("--file_from", required=True)
    cmd_diff.add_argument("--prefix_from", default=None)
    cmd_diff.add_argument("--format_to", required=True)
    cmd_diff.add_argument("--file_to", required=True)
    cmd_diff.add_argument("--prefix_to", default=None)
    cmd_diff.set_defaults(fn=run_cmd_convert)

    cms_sync_dirs = cmd.add_parser("sync_dirs")
    cms_sync_dirs.add_argument("--dir_cmus", required=True)
    cms_sync_dirs.add_argument("--dir_m3u8", required=True)
    cms_sync_dirs.add_argument("--dir_sync_cache", required=True)
    cms_sync_dirs.add_argument("--cmus_prefix", required=True)
    cms_sync_dirs.set_defaults(fn=run_cmd_sync_dirs)

    return ap.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s:%(levelname)s:%(message)s",
    )
    args = parse_args()
    args.fn(args)
