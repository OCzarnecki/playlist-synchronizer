from dataclasses import dataclass
import json
import os


@dataclass
class Track:
    relative_path: str
    display_name: str
    runtime_s: int | None


@dataclass
class Playlist:
    tracks: list[Track]

    def relative_track_paths_equal(self, other):
        return (
            len(self.tracks) == len(other.tracks)
            and all(
                my_track.relative_path == other_track.relative_path
                for my_track, other_track in zip(self.tracks, other.tracks)
            )
        )

    def write_m3u8(self, file):
        file.write('#EXTM3U\n')
        for track in self.tracks:
            file.write(f'#EXTINF:{track.runtime_s if track.runtime_s is not None else -1},{track.display_name}\n')
            file.write(f'{track.relative_path}\n')

    def write_cmus(self, file, music_location):
        """Write a cmus-compatible playlist file."""
        for track in self.tracks:
            full_path = os.path.join(music_location, track.relative_path)
            file.write(f"{full_path}\n")

    def write_cache(self, file):
        """Serialize playlist to JSON format."""
        cache_data = {
            "version": 1,
            "tracks": [
                {
                    "relative_path": track.relative_path,
                    "display_name": track.display_name,
                    "runtime_s": track.runtime_s
                }
                for track in self.tracks
            ]
        }

        json.dump(cache_data, file, indent=2)
