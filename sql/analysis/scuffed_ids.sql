WITH
    rs_filtered AS (
        SELECT
            raw_artist,
            raw_title,
            album_id,
            rs_rank,
            UNNEST (artist_ids) artist_id,
            writers,
            description
        FROM
            rstop500.rs_master_data
        WHERE
            data_type = 'album'
    ),
    grouped_cte AS (
        SELECT
            artist_id,
            raw_artist,
            COUNT(artist_id) AS counter
        FROM
            rs_filtered
        GROUP BY
            artist_id,
            raw_artist
        ORDER BY
            counter DESC
    )
    -- SCUFFED IDs:
    -- artist_id = '2sOghMUmcLv5hDF9IDiu5v';
    -- artist_id = '1fuyJoue5Ew9U8wxon3rs4';
    -- artist_id = '0LyfQWJT6nXafLPZqxe9Of';
    -- artist_id = '65e1Cbe2aHPAXiLWBJaYbk';
SELECT
    *
FROM
    rs_filtered
WHERE
    artist_id IN (
        '2sOghMUmcLv5hDF9IDiu5v',
        '1fuyJoue5Ew9U8wxon3rs4',
        '0LyfQWJT6nXafLPZqxe9Of',
        '65e1Cbe2aHPAXiLWBJaYbk'
    )
ORDER BY
    artist_id DESC;

SELECT
    *
FROM
    rstop500.rs_master_data
WHERE
    raw_title = 'Renaissance';