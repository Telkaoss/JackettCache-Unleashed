Script Overview:
This script, which we can call "CacheFlow: From Jackett to Real-Debrid", automates the process of fetching torrent information from Jackett's cache and adding selected torrents to your Real-Debrid account. It filters torrents based on categories (movies and TV shows) and can optionally filter by a specific tracker.
Environment Variables (.env file):

```
JACKETT_BASE_URL
Purpose: Specifies the URL where your Jackett instance is running.
Example: JACKETT_BASE_URL=http://localhost:9117

JACKETT_API_KEY
Purpose: Your unique API key for accessing Jackett.
Example: JACKETT_API_KEY=abcdef1234567890

JACKETT_ADMIN_PASSWORD
Purpose: The admin password for your Jackett instance.
Example: JACKETT_ADMIN_PASSWORD=your_secure_password

REAL_DEBRID_API_KEY
Purpose: Your API key for accessing Real-Debrid services.
Example: REAL_DEBRID_API_KEY=your_real_debrid_api_key

MOVIE_TV_CATEGORIES
Purpose: Defines which Jackett categories to consider (usually movies and TV shows).
Example: MOVIE_TV_CATEGORIES=2000,5000

MAX_ADDS_PER_MINUTE
Purpose: Limits how many torrents can be added to Real-Debrid per minute.
Example: MAX_ADDS_PER_MINUTE=5

WAIT_TIME_SECONDS
Purpose: Sets the wait time between processing each torrent.
Example: WAIT_TIME_SECONDS=12

RD_DOWNLOADED_STATUS
Purpose: Defines the status string that Real-Debrid uses for downloaded torrents.
Example: RD_DOWNLOADED_STATUS=downloaded

TRACKER_DOMAIN
Purpose: Optionally specifies a tracker domain to filter torrents.
Example: TRACKER_DOMAIN=ygg.re
Note: If left empty, the script will process torrents from all trackers.
```

Script Workflow:

The script connects to Jackett using the provided credentials.
It retrieves the cache of recent torrents from Jackett.
For each torrent in the cache:

It checks if the torrent belongs to the specified categories (movies or TV shows).
If a tracker domain is specified, it filters torrents from that tracker.
It downloads the .torrent file.
It checks if the torrent is already cached on Real-Debrid.
If cached and not already in your account, it adds the torrent to your Real-Debrid account.


The script waits for a specified time between processing each torrent to avoid overloading the APIs.
Finally, it saves a CSV file with the results of the operation.

This script allows you to automate the process of finding and adding torrents to Real-Debrid, focusing on your preferred content types and potentially a specific tracker, all while respecting rate limits and avoiding duplicates.
