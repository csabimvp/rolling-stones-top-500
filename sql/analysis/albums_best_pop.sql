WITH
    artist_genres AS (
        SELECT
            artist_id,
            artist_name,
            array_length (albums, 1) AS number_of_albums,
            total_followers,
            popularity,
            UNNEST (genres) AS Genre,
            UNNEST (albums) AS album_id
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
            album_id,
            ARRAY_AGG (Genre) OVER (
                PARTITION BY
                    artist_id
            ) as filter_genres
        FROM
            artist_genres
        WHERE
            Genre IN ('hip hop', 'pop', 'rap', 'r&b')
    ),
    albums_cte AS (
        SELECT
            album_name,
            album_id,
            rs_rank AS album_ranking,
            popularity,
            released_year,
            label,
            uri
        FROM
            rstop500.albums
        WHERE
            rs_rank > 0
    )
SELECT
    c1.artist_name,
    c2.album_name,
    c2.album_ranking,
    c1.total_followers,
    c1.popularity,
    c2.released_year,
    c2.label,
    c1.filter_genres,
    c2.uri
FROM
    artists_cte AS c1
    INNER JOIN albums_cte AS c2 USING (album_id)
ORDER BY
    -- c1.artist_name ASC,
    c2.album_ranking DESC;