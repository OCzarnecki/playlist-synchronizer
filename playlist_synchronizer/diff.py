from playlist_synchronizer.data import Track, Playlist


def calculate_diff(left: Playlist, right: Playlist):
    def distance(track_left: Track, track_right: Track):
        if track_left.relative_path == track_right.relative_path:
            return 0
        else:
            return 1

    distance_table = [[(0, -1, -1)] * len(right.tracks)] * len(left.tracks)
    distance_table[0][0] = (
        distance(left.tracks[0], right.tracks[0]),
        -1,
        -1,
    )
    for idx_left in range(1, len(left.tracks)):
        distance_table[idx_left][0] = (
            1 + distance_table[idx_left - 1][0][0],
            idx_left - 1,
            0,
        )
    for idx_right in range(1, len(right.tracks)):
        distance_table[0][idx_right] = (
            1 + distance_table[0][idx_right - 1][0],
            0,
            idx_right - 1,
        )

    for idx_left in range(1, len(left.tracks)):
        for idx_right in range(1, len(right.tracks)):
            cost_align_both = (
                distance_table[idx_left - 1][idx_right - 1][0]
                + distance(
                    left.tracks[idx_left],
                    right.tracks[idx_right],
                )
            )
            cost_left_over_blank = distance_table[idx_left - 1][idx_right][0] + 1
            cost_right_over_blank = distance_table[idx_left][idx_right - 1][0] + 1
            min_cost = min(
                cost_align_both,
                cost_left_over_blank,
                cost_right_over_blank,
            )
            if min_cost == cost_align_both:
                cause = (idx_left - 1, idx_right - 1)
            elif min_cost == cost_left_over_blank:
                cause = (idx_left - 1, idx_right)
            else:
                cause = (idx_left, idx_right - 1)
            distance_table[idx_left][idx_right] = (min_cost, *cause)

    coords = (len(left.tracks) - 1, len(right.tracks) - 1)
    backtrack = []
    while coords != (-1, -1):
        previous = distance_table[coords[0]][coords[1]][1]
        ...  # None of this is needed (maybe), we just want to merge

    return distance_table[len(left.tracks) - 1][len(right.tracks) - 1]
