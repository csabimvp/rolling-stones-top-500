-- sudo su postgres
-- psql
CREATE DATABASE rolling_stones OWNER csabimvp;

-- \q
-- psql -U csabimvp -d rolling_stones
CREATE SCHEMA rstop500 AUTHORIZATION csabimvp;

CREATE TABLE
    IF NOT EXISTS rstop500.tracks (
        track_id VARCHAR PRIMARY KEY,
        track_name VARCHAR,
        artist_ids VARCHAR ARRAY,
        rs_rank INTEGER,
        is_explicit BOOLEAN,
        popularity NUMERIC,
        duration_ms NUMERIC,
        track_number_on_album NUMERIC,
        external_url VARCHAR,
        uri VARCHAR,
        release_year INTEGER
        -- album_id VARCHAR REFERENCES rstop500.albums
    );

CREATE TABLE
    IF NOT EXISTS rstop500.artists (
        artist_id VARCHAR PRIMARY KEY,
        artist_name VARCHAR,
        albums VARCHAR ARRAY,
        genres VARCHAR ARRAY,
        total_followers NUMERIC,
        popularity NUMERIC,
        external_url VARCHAR,
        uri VARCHAR
    );

CREATE TABLE
    IF NOT EXISTS rstop500.albums (
        album_id VARCHAR PRIMARY KEY,
        album_name VARCHAR,
        rs_rank INTEGER,
        popularity NUMERIC,
        total_tracks NUMERIC,
        label VARCHAR,
        release_year INTEGER,
        album_image VARCHAR,
        external_url VARCHAR,
        uri VARCHAR,
        artist_ids VARCHAR ARRAY
        -- track_id VARCHAR REFERENCES rstop500.tracks,
    );

ALTER TABLE rstop500.tracks ADD album_id VARCHAR REFERENCES rstop500.albums;

-- ALTER TABLE rstop500.albums ADD track_id VARCHAR REFERENCES rstop500.tracks;
-- ALTER TABLE rstop500.albums ADD artist_id VARCHAR REFERENCES rstop500.artists;
-- \q
-- exit