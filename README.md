Script Overview:
This script, which we can call "JackettCache-Unleashed: From Jackett to Real-Debrid", automates the process of fetching torrent information from Jackett's cache and adding selected torrents to your Real-Debrid account. It filters torrents based on categories (movies and TV shows) and can optionally filter by a specific tracker.
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


Certainly! I'll explain the installation method for GitHub in English, step by step.
Installation Method for GitHub:

Clone the Repository:

Open a terminal or command prompt.
Navigate to the directory where you want to install the project.
Run the following command:


The script waits for a specified time between processing each torrent to avoid overloading the APIs.
Finally, it saves a CSV file with the results of the operation.

This script allows you to automate the process of finding and adding torrents to Real-Debrid, focusing on your preferred content types and potentially a specific tracker, all while respecting rate limits and avoiding duplicates.


Certainly! I'll explain the installation method for GitHub in English, step by step.



Installation Method :

1. Clone the Repository:
   - Open a terminal or command prompt.
   - Navigate to the directory where you want to install the project.
   - Run the following command:
     ```
     git clone https://github.com/your-username/your-repo-name.git
     ```
   - Replace `your-username` and `your-repo-name` with the actual GitHub username and repository name.

2. Navigate to the Project Directory:
   ```
   cd your-repo-name
   ```

3. Set Up a Virtual Environment (Optional but Recommended):
   - For Python 3:
     ```
     python3 -m venv venv
     ```
   - Activate the virtual environment:
     - On Windows: `venv\Scripts\activate`
     - On macOS and Linux: `source venv/bin/activate`

4. Install Dependencies:
   - Ensure you have a `requirements.txt` file in your repository with all necessary dependencies.
   - Run:
     ```
     pip install -r requirements.txt
     ```

5. Set Up Environment Variables:
   - Create a `.env` file in the project root directory.
   - Add your configuration variables to this file:
     ```
     JACKETT_BASE_URL=http://your-jackett-url:port
     JACKETT_API_KEY=your-jackett-api-key
     JACKETT_ADMIN_PASSWORD=your-jackett-password
     REAL_DEBRID_API_KEY=your-real-debrid-api-key
     MOVIE_TV_CATEGORIES=2000,5000
     MAX_ADDS_PER_MINUTE=5
     WAIT_TIME_SECONDS=12
     RD_DOWNLOADED_STATUS=downloaded
     TRACKER_DOMAIN=ygg.re
     ```
   - Replace the values with your actual configuration.

6. Docker Setup (if using Docker):
   - Ensure Docker and Docker Compose are installed on your system.
   - The repository should include a `Dockerfile` and `docker-compose.yml`.
   - Build and run the Docker container:
     ```
     docker-compose up --build
     ```

7. Run the Script:
   - If not using Docker, run:
     ```
     python scraper.py
     ```
   - The script will start running based on your configuration in the `.env` file.

8. Check the Results:
   - After the script finishes, check the `results.csv` file in the `/data` directory for the operation results.

Additional Notes:
- Ensure that your Jackett and Real-Debrid accounts are properly set up and accessible.
- Keep your API keys and passwords secure and never share them publicly.
- Regularly check for updates to the repository and update your local copy:
  ```
  git pull origin main
  ```

This installation method allows users to easily set up and run your script from a GitHub repository, with the flexibility to configure it for their specific needs using environment variables.
