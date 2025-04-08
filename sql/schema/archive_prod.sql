INSERT INTO
    archived.rs_master_data
SELECT
    *
FROM
    rstop500.rs_master_data;

INSERT INTO
    archived.tracks (
        track_id,
        track_name,
        artist_ids,
        rs_rank,
        is_explicit,
        popularity,
        duration_ms,
        track_number_on_album,
        external_url,
        uri,
        released_year
    )
SELECT
    track_id,
    track_name,
    artist_ids,
    rs_rank,
    is_explicit,
    popularity,
    duration_ms,
    track_number_on_album,
    external_url,
    uri,
    released_year
FROM
    rstop500.tracks;

INSERT INTO
    archived.artists
SELECT
    *
FROM
    rstop500.artists;

INSERT INTO
    archived.albums (
        album_id,
        album_name,
        rs_rank,
        popularity,
        total_tracks,
        label,
        released_year,
        album_image,
        external_url,
        uri,
        artist_ids
    )
SELECT
    album_id,
    album_name,
    rs_rank,
    popularity,
    total_tracks,
    label,
    released_year,
    album_image,
    external_url,
    uri,
    artist_ids
FROM
    rstop500.albums;