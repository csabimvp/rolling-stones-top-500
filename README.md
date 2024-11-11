# rolling-stones-top-500

Purpose of this project is to scrape the Rolling Stones Top 500 Albums and Songs and then enrich the data via the Spotify API, finally to store that data in a database. Eventually use it as a base for an artist/song recommendation engine.

## Greates songs of All time:
https://www.rollingstone.com/music/music-lists/best-songs-of-all-time-1224767/

## Greates albums of All time:
https://www.rollingstone.com/music/music-lists/best-albums-of-all-time-1062063/


## Project Scope:
Crate initial database for songs and albums. 


## Spotify API logic:
1) We need to use the search endpoint to search for the Spotify artist/track ID
    - From that we can pull the Artist, Album and Track IDs for further API calls.
2) Then we can use the ID to query the Get Artist/Get Track api to enrich the data.


## Database
Tables
- Artist
- Tracks
- Albums


## Future Improvements:
1) Use this link https://developer.spotify.com/documentation/web-api/reference/get-an-artists-related-artists to pull related Artists,
2) Create Spotify Playlists for the Greatest Songs of All Time