WITH
    artist_genres AS (
        SELECT
            artist_id,
            artist_name,
            array_length (albums, 1) AS number_of_albums,
            total_followers,
            popularity,
            UNNEST (genres) AS Genre
        FROM
            rstop500.artists
    ),
    artists_cte AS (
        SELECT DISTINCT
            artist_id,
            artist_name,
            number_of_albums,
            total_followers,
            popularity,
            ARRAY_AGG (Genre) OVER (
                PARTITION BY
                    artist_id
            ) as filter_genres
        FROM
            artist_genres
        WHERE
            Genre IN ('hip hop', 'pop', 'rap', 'r&b')
    ),
    tracks_cte AS (
        SELECT
            t1.track_name,
            t1.rs_rank AS track_ranking,
            t1.album_id,
            t1.released_year,
            t1.uri,
            UNNEST (t1.artist_ids) artist_id,
            t2.description
        FROM
            rstop500.tracks AS t1
            INNER JOIN rstop500.rs_master_data AS t2 USING (track_id)
    ),
    albums_cte AS (
        SELECT
            album_name,
            album_id,
            rs_rank AS album_ranking
        FROM
            rstop500.albums
    )
SELECT
    c1.artist_name,
    c1.number_of_albums,
    c1.total_followers,
    c1.popularity,
    c2.track_name,
    c2.track_ranking,
    c3.album_name,
    c3.album_ranking,
    c2.released_year,
    c2.uri,
    c1.filter_genres,
    c2.description
FROM
    artists_cte AS c1
    INNER JOIN tracks_cte AS c2 USING (artist_id)
    INNER JOIN albums_cte AS c3 USING (album_id)
ORDER BY
    c1.artist_name ASC,
    c2.track_ranking DESC;