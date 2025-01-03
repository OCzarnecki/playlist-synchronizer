import os
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

from playlist_synchronizer.importer import (
    import_cache,
    import_cmus,
    import_m3u8,
)

log = logging.getLogger(__name__)


class ImpossibleActionError(Exception):
    pass


@dataclass
class SyncAction(ABC):
    name: str

    @abstractmethod
    def run(self, cmus_dir, m3u8_dir, cache_dir, cmus_prefix) -> None: ...


@dataclass
class NewCmus(SyncAction):
    cmus_path: str

    def run(self, cmus_dir, m3u8_dir, cache_dir, cmus_prefix) -> None:
        with open(self.cmus_path, "r") as file:
            playlist = import_cmus(cmus_prefix, file)

        with open(os.path.join(m3u8_dir, self.name + ".m3u8"), "w") as file:
            playlist.write_m3u8(file)

        with open(os.path.join(cache_dir, self.name + ".json"), "w") as file:
            playlist.write_cache(file)


@dataclass
class NewM3u8(SyncAction):
    m3u8_path: str

    def run(self, cmus_dir, m3u8_dir, cache_dir, cmus_prefix) -> None:
        with open(self.m3u8_path, "r") as file:
            playlist = import_m3u8(file)

        with open(os.path.join(cmus_dir, self.name), "w") as file:
            playlist.write_cmus(file, cmus_prefix)

        with open(os.path.join(cache_dir, self.name + ".json"), "w") as file:
            playlist.write_cache(file)


@dataclass
class ThreeWayMerge(SyncAction):
    m3u8_path: str
    cmus_path: str
    cache_path: str

    def run(self, cmus_dir, m3u8_dir, cache_dir, cmus_prefix) -> None:
        with open(self.cache_path, "r") as file:
            cache_playlist = import_cache(file)
        with open(self.m3u8_path, "r") as file:
            m3u8_playlist = import_m3u8(file)
        with open(self.cmus_path, "r") as file:
            cmus_playlist = import_cmus(cmus_prefix, file)
        cmus_matches_base = cmus_playlist.relative_track_paths_equal(cache_playlist)
        m3u8_matches_base = m3u8_playlist.relative_track_paths_equal(cache_playlist)
        if not (cmus_matches_base or m3u8_matches_base):
            raise ValueError(
                "Both cmus and m3u8 have diverged from base. Proper merging "
                + "is not currently implemented."
            )
        elif cmus_matches_base and m3u8_matches_base:
            log.debug("Files are in sync, nothing to do")
        elif cmus_matches_base:
            log.info("Merging %s: cmus is stale", self.name)
            with open(os.path.join(cmus_dir, self.name), "w") as file:
                m3u8_playlist.write_cmus(file, cmus_prefix)

            with open(os.path.join(cache_dir, self.name + ".json"), "w") as file:
                m3u8_playlist.write_cache(file)
        elif m3u8_matches_base:
            log.info("Merging %s: m3u8 is stale", self.name)
            with open(os.path.join(m3u8_dir, self.name + ".m3u8"), "w") as file:
                cmus_playlist.write_m3u8(file)

            with open(os.path.join(cache_dir, self.name + ".json"), "w") as file:
                cmus_playlist.write_cache(file)


@dataclass
class MergeWithoutBase(SyncAction):
    m3u8_path: str
    cmus_path: str

    def run(self, cmus_dir, m3u8_dir, cache_dir, cmus_prefix) -> None:
        raise ValueError(
            "Cannot merge without base. Please reconcile manually and "
            + "delete one of the playlist files."
        )


@dataclass
class DeleteStaleCache(SyncAction):
    cache_path: str

    def run(self, cmus_dir, m3u8_dir, cache_dir, cmus_prefix) -> None:
        os.unlink(self.cache_path)


def get_playlist_files(dir_: str, ext: str) -> dict[str, str]:
    """Returns dict mapping base file name w/o extension to a file path."""
    files = os.listdir(dir_)
    return {
        os.path.splitext(os.path.basename(f))[0]: os.path.join(dir_, f)
        for f in files
        if os.path.isfile(os.path.join(dir_, f))
        and f.endswith(ext)
    }


def plan_sync(
    cmus_dir: str,
    m3u8_dir: str,
    cache_dir: str,
) -> list[SyncAction]:
    cmus_files = get_playlist_files(cmus_dir, "")
    m3u8_files = get_playlist_files(m3u8_dir, ".m3u8")
    cache_files = get_playlist_files(cache_dir, ".json")
    all_playlist_names = (
        set(cmus_files.keys())
        | set(m3u8_files.keys())
        | set(cache_files.keys())
    )
    log.debug("Found playlists: %s", all_playlist_names)
    actions = []
    for name in all_playlist_names:
        if name in cmus_files and name not in m3u8_files:
            actions.append(
                NewCmus(name, cmus_files[name])
            )
        elif name not in cmus_files and name in m3u8_files:
            actions.append(
                NewM3u8(name, m3u8_files[name])
            )
        elif name in cmus_files and name in m3u8_files:
            if name in cache_files:
                actions.append(
                    ThreeWayMerge(
                        name,
                        m3u8_files[name],
                        cmus_files[name],
                        cache_files[name],
                    )
                )
            else:
                actions.append(
                    MergeWithoutBase(
                        name,
                        m3u8_files[name],
                        cmus_files[name],
                    )
                )
        else:
            actions.append(
                DeleteStaleCache(name, cache_files[name])
            )
    return actions


def sync_dirs(
    cmus_dir: str,
    m3u8_dir: str,
    cache_dir: str,
    cmus_prefix: str,
):
    os.makedirs(cache_dir, exist_ok=True)
    actions = plan_sync(cmus_dir, m3u8_dir, cache_dir)
    for action in actions:
        log.debug("Running %s", action)
        action.run(cmus_dir, m3u8_dir, cache_dir, cmus_prefix)
