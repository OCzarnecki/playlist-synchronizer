import json
import os.path

from playlist_synchronizer.data import Track, Playlist


class PlaylistImporterException(Exception):
    pass


def import_m3u8(file):
    # lines = file.readlines()
    start = next(file).strip()
    if start[0] == "\ufeff":
        start = start[1:]
    if not start == "#EXTM3U":
        raise PlaylistImporterException(
            "An m3u8 playlist must start with #EXTM3U"
        )

    play_time = -1
    display_title = ""
    tracks = []
    for line in file:
        if line.startswith("#"):
            tokens = line.strip().split(":")
            if tokens[0] in [
                "#PLAYLIST",
                "#EXTGRP",
                "#EXTALB",
                "#EXTART",
                "#EXTGENRE",
                "#EXTM3A",
                "#EXTBYT",
                "#EXTBIN",
                "#EXTENC",
                "#EXTIMG",
            ]:
                continue
            if tokens[0] == "#EXTINF":
                info_tokens = tokens[1].split(",", 2)
                if len(info_tokens) == 1:
                    display_title = info_tokens[0]
                elif len(info_tokens) == 2:
                    play_time = info_tokens[0]
                    display_title = info_tokens[1]
        else:
            rel_path = line.strip()
            tracks.append(Track(
                relative_path=rel_path,
                display_name=display_title,
                runtime_s=play_time,
            ))
            display_title = ""
            play_time = -1
    return Playlist(tracks)


def import_cmus(prefix, file):
    tracks = []
    for line in file:
        path = line.strip()
        display_title, _ext = os.path.splitext(
            os.path.basename(path)
        )
        tracks.append(Track(
            relative_path=path.removeprefix(prefix),
            display_name=display_title,
            runtime_s=-1,
        ))
    return Playlist(tracks)


def import_cache(file):
    "Deserialize playlist from JSON format."
    cache_data = json.load(file)

    if cache_data.get("version") != 1:
        raise ValueError("Unsupported cache version")

    playlist = Playlist(
        tracks=[
            Track(
                relative_path=track["relative_path"],
                display_name=track["display_name"],
                runtime_s=track["runtime_s"]
            )
            for track in cache_data["tracks"]
        ]
    )

    return playlist
