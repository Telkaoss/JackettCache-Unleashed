# scraper.py
import requests
import json
import csv
import os
import tempfile
import bencodepy
import hashlib
import time
from urllib.parse import unquote, urlparse, urlencode

JACKETT_BASE_URL = os.environ['JACKETT_BASE_URL']
JACKETT_LOGIN_URL = f"{JACKETT_BASE_URL}/UI/Dashboard"
JACKETT_CACHE_URL = f"{JACKETT_BASE_URL}/api/v2.0/indexers/cache"
JACKETT_API_KEY = os.environ['JACKETT_API_KEY']
JACKETT_ADMIN_PASSWORD = os.environ['JACKETT_ADMIN_PASSWORD']
REAL_DEBRID_API_URL = "https://api.real-debrid.com/rest/1.0"
REAL_DEBRID_API_KEY = os.environ['REAL_DEBRID_API_KEY']

MOVIE_TV_CATEGORIES = [2000, 5000]  # 2000 for movies, 5000 for TV shows
TRACKER_DOMAIN = os.environ.get('TRACKER_DOMAIN', 'ygg.re')
MAX_ADDS_PER_MINUTE = int(os.environ.get('MAX_ADDS_PER_MINUTE', 5))
WAIT_TIME = float(os.environ.get('WAIT_TIME_SECONDS', 12))

def login_to_jackett():
    session = requests.Session()
    login_data = {"password": JACKETT_ADMIN_PASSWORD}
    response = session.post(JACKETT_LOGIN_URL, data=login_data)
    if response.status_code == 200:
        print("Successfully logged in to Jackett")
        return session
    else:
        print(f"Failed to log in to Jackett. Status code: {response.status_code}")
        return None

def get_jackett_cache(session):
    headers = {"X-Api-Key": JACKETT_API_KEY}
    try:
        response = session.get(JACKETT_CACHE_URL, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error while querying Jackett: {e}")
        return None

def get_torrent_hash(torrent_file_path):
    with open(torrent_file_path, 'rb') as f:
        metadata = bencodepy.decode(f.read())
        info = metadata[b'info']
        return hashlib.sha1(bencodepy.encode(info)).hexdigest().lower()

def create_magnet_link(torrent_hash, name):
    base_url = "magnet:?"
    xt = f"xt=urn:btih:{torrent_hash}"
    dn = f"dn={urlencode({'': name})[1:]}"  # Remove leading '=' from urlencode result
    tr = "tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80"
    return f"{base_url}{xt}&{dn}&{tr}"

def check_torrent_status_on_rd(torrent_hash, headers):
    try:
        response = requests.get(f"{REAL_DEBRID_API_URL}/torrents/instantAvailability/{torrent_hash}", headers=headers)
        response.raise_for_status()
        availability = response.json()
        
        if isinstance(availability, list):
            availability = availability[0] if availability else {}
        
        if torrent_hash in availability:
            torrent_info = availability[torrent_hash]
            if isinstance(torrent_info, list):
                for item in torrent_info:
                    if isinstance(item, dict) and item.get('rd'):
                        return "downloaded"
            elif isinstance(torrent_info, dict) and torrent_info.get('rd'):
                return "downloaded"
        
        return "not_available"
    except requests.RequestException as e:
        print(f"Error while checking torrent status on Real-Debrid: {e}")
        return "error"

def is_torrent_already_added(torrent_hash, headers):
    try:
        response = requests.get(f"{REAL_DEBRID_API_URL}/torrents", headers=headers)
        response.raise_for_status()
        torrents = response.json()
        return any(torrent['hash'].lower() == torrent_hash.lower() for torrent in torrents)
    except requests.RequestException as e:
        print(f"Error while checking existing torrents: {e}")
        return False

def add_torrent_to_real_debrid(torrent_file_path, name):
    headers = {
        "Authorization": f"Bearer {REAL_DEBRID_API_KEY}"
    }
    
    try:
        print(f"Checking status for: {name}")
        torrent_hash = get_torrent_hash(torrent_file_path)
        
        if is_torrent_already_added(torrent_hash, headers):
            print(f"Torrent is already present on your Real-Debrid account: {name}")
            return True
        
        status = check_torrent_status_on_rd(torrent_hash, headers)
        
        if status != "downloaded":
            print(f"The torrent is not available on Real-Debrid or not yet downloaded.")
            return False
        
        print(f"The torrent is available. Adding to your account...")
        magnet_link = create_magnet_link(torrent_hash, name)
        
        add_data = {"magnet": magnet_link}
        add_response = requests.post(f"{REAL_DEBRID_API_URL}/torrents/addMagnet", headers=headers, data=add_data)
        
        add_response.raise_for_status()
        response_data = add_response.json()
        
        if 'id' in response_data:
            torrent_id = response_data['id']
            print(f"Torrent successfully added. ID: {torrent_id}")
            return select_all_files_and_start_torrent(torrent_id, headers)
        else:
            print(f"Unexpected response from Real-Debrid: {response_data}")
            return False
    except requests.RequestException as e:
        print(f"Error while adding the torrent: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error details: {e.response.text}")
        return False

def select_all_files_and_start_torrent(torrent_id, headers):
    try:
        torrent_info_response = requests.get(f"{REAL_DEBRID_API_URL}/torrents/info/{torrent_id}", headers=headers)
        torrent_info_response.raise_for_status()
        torrent_info = torrent_info_response.json()

        all_file_ids = [str(file['id']) for file in torrent_info['files']]
        select_files_data = {"files": ",".join(all_file_ids)}
        select_files_response = requests.post(f"{REAL_DEBRID_API_URL}/torrents/selectFiles/{torrent_id}", headers=headers, data=select_files_data)
        select_files_response.raise_for_status()
        print(f"All files selected: {len(all_file_ids)} files")

        torrent_info_response = requests.get(f"{REAL_DEBRID_API_URL}/torrents/info/{torrent_id}", headers=headers)
        torrent_info_response.raise_for_status()
        torrent_info = torrent_info_response.json()
        selected_files = [f for f in torrent_info['files'] if f['selected']]
        print(f"Files actually selected: {len(selected_files)}/{len(torrent_info['files'])}")

        return len(selected_files) == len(torrent_info['files'])
    except requests.RequestException as e:
        print(f"Error while selecting files: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error details: {e.response.text}")
        return False

def save_to_csv(results, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['title', 'size', 'seeders', 'peers', 'added_to_rd'])
        writer.writeheader()
        for result in results:
            writer.writerow(result)

def download_torrent_file(session, link):
    try:
        print(f"Downloading .torrent file from: {link}")
        response = session.get(link, allow_redirects=True)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        print(f"Received Content-Type: {content_type}")
        
        if 'application/x-bittorrent' in content_type:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.torrent') as tmp_file:
                tmp_file.write(response.content)
                return tmp_file.name
        else:
            print(f"The downloaded content is not a valid torrent file. Content-Type: {content_type}")
            return None
    except requests.RequestException as e:
        print(f"Error while downloading the .torrent file: {e}")
        return None

def is_movie_or_tv(result):
    return any(cat in MOVIE_TV_CATEGORIES for cat in result.get('Category', []))

def is_from_tracker(result):
    details_url = result.get('Details', '')
    return TRACKER_DOMAIN in urlparse(details_url).netloc

def main():
    print("Connecting to Jackett")
    session = login_to_jackett()
    if not session:
        return

    print("Retrieving Jackett cache")
    cache_results = get_jackett_cache(session)

    if not cache_results:
        print("No valid results found in Jackett cache")
        return

    processed_results = []
    for result in cache_results:
        if not (is_movie_or_tv(result) and is_from_tracker(result)):
            continue

        print(f"\nProcessing: {result['Title']}")
        print(f"Category: {result.get('Category')}")
        print(f"Source: {result.get('Details', 'Unknown')}")
        print(f"Link: {result.get('Link', 'Not available')}")

        torrent_file_path = download_torrent_file(session, result['Link'])
        
        if torrent_file_path:
            added_to_rd = add_torrent_to_real_debrid(torrent_file_path, result['Title'])
            if added_to_rd:
                print(f"Torrent successfully added to Real-Debrid: {result['Title']}")
            else:
                print(f"Failed to add torrent to Real-Debrid: {result['Title']}")
            os.unlink(torrent_file_path)  # Delete temporary file
        else:
            print("Unable to obtain the .torrent file.")
            added_to_rd = False

        processed_result = {
            "title": result["Title"],
            "size": result.get("Size", "Unknown"),
            "seeders": result.get("Seeders", "Unknown"),
            "peers": result.get("Peers", "Unknown"),
            "added_to_rd": "Yes" if added_to_rd else "No"
        }
        processed_results.append(processed_result)

        print(f"Waiting {WAIT_TIME:.2f} seconds before the next addition...")
        time.sleep(WAIT_TIME)

    save_to_csv(processed_results, "/data/results.csv")
    print("Jackett cache processing and addition to Real-Debrid completed. Results saved in /data/results.csv")

if __name__ == "__main__":
    main()
