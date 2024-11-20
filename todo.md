## To Do's

1) Review db schema to make sure everything is working.
Match dataclass keys with the postgres table schemas.

2) We need to implement batch API querying to avoid API timeouts and bans and increase performance.

Loop trough the top 500 songs and albums and fetch the search API. Find best search match with #3 step below. Store Track ID, Album ID and Artist IDs. Ideally we would store the Rolling Stones Top 500 data with the Spotify Search API data. (to have rank and the text as well)

Once we have all the sets of IDs we can batch pull all the tracks, albums and artists.

How are we matching the returned batch data back to the Rolling Stones data? - Actually we don't have to... SQL will do it for us.

**We need one extra dataclass that has to be loaded to postgres, therefore one more postgres table too. Capture rolling stones data and spotify search at the same dataclas..**


3) Somehow check result against search query. Maybe try to implement this algorithm:

check against all returned search results and select the maximum from the list. That's the closest match for the search query.
url: https://www.geeksforgeeks.org/python-similarity-metrics-of-strings/

```python
import difflib
#This code calculates the similarity between two strings using the ndiff method from the difflib library. 
def compute_similarity(input_string, reference_string):
#The ndiff method returns a list of strings representing the differences between the two input strings.
	diff = difflib.ndiff(input_string, reference_string)
	diff_count = 0
	for line in diff:
	# a "-", indicating that it is a deleted character from the input string.
		if line.startswith("-"):
			diff_count += 1
    # calculates the similarity by subtracting the ratio of the number of deleted characters to the length of the input string from 1
	return 1 - (diff_count / len(input_string))

input_string = "Geeksforgeeks"
reference_string = "Geeks4geeks"
similarity = compute_similarity(input_string, reference_string)
print(similarity)
#This code is contributed by Edula Vinay Kumar Reddy
```
