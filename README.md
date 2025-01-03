# Script for keeping cmus and m3u8 playlists in sync

Cmus defines playlists with an absolute path. To infer the relative path, a `cmus_prefix` is needed.


# Usage

```
python -m playlist_synchronizer sync_dirs \
    --dir_cmus ~/.config/cmus/playlists \
    --cmus_prefix /home/user/Music \
    --dir_m3u8 /home/user/Music \
    --dir_sync_cache ~/.cache/playlist_cache
```
