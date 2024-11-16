-- sudo su postgres
-- psql
CREATE DATABASE rolling_stones OWNER csabimvp;

-- \q
-- psql -U csabimvp -d rolling_stones
CREATE SCHEMA rstop500 AUTHORIZATION csabimvp;

CREATE TABLE
    IF NOT EXISTS rstop500.tracks (
        track_id VARCHAR NOT NULL PRIMARY KEY,
        track_name VARCHAR NOT NULL,
        artist_ids VARCHAR ARRAY,
        rs_rank INTEGER NOT NULL,
        is_explicit BOOLEAN,
        popularity NUMERIC,
        duration NUMERIC,
        track_number_on_album NUMERIC,
        external_url VARCHAR
        -- album_id VARCHAR REFERENCES rstop500.albums
        -- artist_id VARCHAR ARRAY REFERENCES rstop500.artists,
    );

CREATE TABLE
    IF NOT EXISTS rstop500.artists (
        artist_id VARCHAR NOT NULL PRIMARY KEY,
        artist_name VARCHAR NOT NULL,
        genres VARCHAR ARRAY,
        popularity NUMERIC,
        total_followers NUMERIC,
        external_url VARCHAR,
        albums VARCHAR ARRAY
    );

CREATE TABLE
    IF NOT EXISTS rstop500.albums (
        album_id VARCHAR NOT NULL PRIMARY KEY,
        album_name VARCHAR NOT NULL,
        rs_rank INTEGER NOT NULL,
        genres VARCHAR ARRAY,
        popularity NUMERIC,
        total_tracks NUMERIC,
        external_url VARCHAR,
        label VARCHAR
        -- artist_id VARCHAR,
        -- track_id VARCHAR NOT NULL REFERENCES rstop500.tracks,
    );

ALTER TABLE rstop500.tracks ADD album_id VARCHAR REFERENCES rstop500.albums;

ALTER TABLE rstop500.albums ADD artist_id VARCHAR NOT NULL REFERENCES rstop500.artists;

ALTER TABLE rstop500.albums ADD track_id VARCHAR NOT NULL REFERENCES rstop500.tracks;