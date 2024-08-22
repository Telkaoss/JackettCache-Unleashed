# scraper.py
import requests
import json
import csv
import os
import tempfile
import bencodepy
import hashlib
import time
import schedule
from urllib.parse import unquote, urlparse, urlencode

# Configuration à partir des variables d'environnement
JACKETT_BASE_URL = os.environ['JACKETT_BASE_URL']
JACKETT_LOGIN_URL = f"{JACKETT_BASE_URL}/UI/Dashboard"
JACKETT_CACHE_URL = f"{JACKETT_BASE_URL}/api/v2.0/indexers/cache"
JACKETT_API_KEY = os.environ['JACKETT_API_KEY']
JACKETT_ADMIN_PASSWORD = os.environ['JACKETT_ADMIN_PASSWORD']
REAL_DEBRID_API_URL = "https://api.real-debrid.com/rest/1.0"
REAL_DEBRID_API_KEY = os.environ['REAL_DEBRID_API_KEY']

# Paramètres configurables
MOVIE_TV_CATEGORIES = [int(cat) for cat in os.environ['MOVIE_TV_CATEGORIES'].split(',')]
MAX_ADDS_PER_MINUTE = int(os.environ.get('MAX_ADDS_PER_MINUTE', 5))
WAIT_TIME = float(os.environ.get('WAIT_TIME_SECONDS', 12))
RD_DOWNLOADED_STATUS = os.environ['RD_DOWNLOADED_STATUS']
TRACKER_DOMAIN = os.environ.get('TRACKER_DOMAIN', '')

def login_to_jackett():
    """Se connecte à Jackett et retourne une session."""
    session = requests.Session()
    login_data = {"password": JACKETT_ADMIN_PASSWORD}
    response = session.post(JACKETT_LOGIN_URL, data=login_data)
    if response.status_code == 200:
        print("Connexion à Jackett réussie")
        return session
    else:
        print(f"Échec de la connexion à Jackett. Code d'état : {response.status_code}")
        return None

def get_jackett_cache(session):
    """Récupère le cache de Jackett."""
    headers = {"X-Api-Key": JACKETT_API_KEY}
    try:
        response = session.get(JACKETT_CACHE_URL, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Erreur lors de la requête à Jackett: {e}")
        return None

def get_torrent_hash(torrent_file_path):
    """Calcule le hash d'un fichier torrent."""
    with open(torrent_file_path, 'rb') as f:
        metadata = bencodepy.decode(f.read())
        info = metadata[b'info']
        return hashlib.sha1(bencodepy.encode(info)).hexdigest().lower()

def create_magnet_link(torrent_hash, name):
    """Crée un lien magnet à partir du hash et du nom du torrent."""
    base_url = "magnet:?"
    xt = f"xt=urn:btih:{torrent_hash}"
    dn = f"dn={urlencode({'': name})[1:]}"
    tr = "tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80"
    return f"{base_url}{xt}&{dn}&{tr}"

def check_torrent_status_on_rd(torrent_hash, headers):
    """Vérifie le statut d'un torrent sur Real-Debrid."""
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
                        return RD_DOWNLOADED_STATUS
            elif isinstance(torrent_info, dict) and torrent_info.get('rd'):
                return RD_DOWNLOADED_STATUS
        
        return "not_available"
    except requests.RequestException as e:
        print(f"Erreur lors de la vérification du statut sur Real-Debrid: {e}")
        return "error"

def is_torrent_already_added(torrent_hash, headers):
    """Vérifie si un torrent est déjà ajouté à Real-Debrid."""
    try:
        response = requests.get(f"{REAL_DEBRID_API_URL}/torrents", headers=headers)
        response.raise_for_status()
        torrents = response.json()
        return any(torrent['hash'].lower() == torrent_hash.lower() for torrent in torrents)
    except requests.RequestException as e:
        print(f"Erreur lors de la vérification des torrents existants: {e}")
        return False

def add_torrent_to_real_debrid(torrent_file_path, name):
    """Ajoute un torrent à Real-Debrid."""
    headers = {
        "Authorization": f"Bearer {REAL_DEBRID_API_KEY}"
    }
    
    try:
        print(f"Vérification du statut pour: {name}")
        torrent_hash = get_torrent_hash(torrent_file_path)
        
        if is_torrent_already_added(torrent_hash, headers):
            print(f"Le torrent est déjà présent sur votre compte Real-Debrid: {name}")
            return True
        
        status = check_torrent_status_on_rd(torrent_hash, headers)
        
        if status != RD_DOWNLOADED_STATUS:
            print(f"Le torrent n'est pas disponible sur Real-Debrid ou n'est pas encore téléchargé.")
            return False
        
        print(f"Le torrent est disponible. Ajout à votre compte...")
        magnet_link = create_magnet_link(torrent_hash, name)
        
        add_data = {"magnet": magnet_link}
        add_response = requests.post(f"{REAL_DEBRID_API_URL}/torrents/addMagnet", headers=headers, data=add_data)
        
        add_response.raise_for_status()
        response_data = add_response.json()
        
        if 'id' in response_data:
            torrent_id = response_data['id']
            print(f"Torrent ajouté avec succès. ID: {torrent_id}")
            return select_all_files_and_start_torrent(torrent_id, headers)
        else:
            print(f"Réponse inattendue de Real-Debrid: {response_data}")
            return False
    except requests.RequestException as e:
        print(f"Erreur lors de l'ajout du torrent: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Détails de l'erreur: {e.response.text}")
        return False

def select_all_files_and_start_torrent(torrent_id, headers):
    """Sélectionne tous les fichiers d'un torrent sur Real-Debrid."""
    try:
        torrent_info_response = requests.get(f"{REAL_DEBRID_API_URL}/torrents/info/{torrent_id}", headers=headers)
        torrent_info_response.raise_for_status()
        torrent_info = torrent_info_response.json()

        all_file_ids = [str(file['id']) for file in torrent_info['files']]
        select_files_data = {"files": ",".join(all_file_ids)}
        select_files_response = requests.post(f"{REAL_DEBRID_API_URL}/torrents/selectFiles/{torrent_id}", headers=headers, data=select_files_data)
        select_files_response.raise_for_status()
        print(f"Tous les fichiers sélectionnés: {len(all_file_ids)} fichiers")

        torrent_info_response = requests.get(f"{REAL_DEBRID_API_URL}/torrents/info/{torrent_id}", headers=headers)
        torrent_info_response.raise_for_status()
        torrent_info = torrent_info_response.json()
        selected_files = [f for f in torrent_info['files'] if f['selected']]
        print(f"Fichiers effectivement sélectionnés: {len(selected_files)}/{len(torrent_info['files'])}")

        return len(selected_files) == len(torrent_info['files'])
    except requests.RequestException as e:
        print(f"Erreur lors de la sélection des fichiers: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Détails de l'erreur: {e.response.text}")
        return False

def save_to_csv(results, filename):
    """Sauvegarde les résultats dans un fichier CSV."""
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['title', 'size', 'seeders', 'peers', 'added_to_rd'])
        writer.writeheader()
        for result in results:
            writer.writerow(result)

def download_torrent_file(session, link):
    """Télécharge un fichier torrent à partir d'un lien."""
    try:
        print(f"Téléchargement du fichier .torrent depuis: {link}")
        response = session.get(link, allow_redirects=True)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        print(f"Content-Type reçu: {content_type}")
        
        if 'application/x-bittorrent' in content_type:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.torrent') as tmp_file:
                tmp_file.write(response.content)
                return tmp_file.name
        else:
            print(f"Le contenu téléchargé n'est pas un fichier torrent valide. Content-Type: {content_type}")
            return None
    except requests.RequestException as e:
        print(f"Erreur lors du téléchargement du fichier .torrent: {e}")
        return None

def is_movie_or_tv(result):
    """Vérifie si un résultat appartient aux catégories films ou séries TV."""
    return any(cat in MOVIE_TV_CATEGORIES for cat in result.get('Category', []))

def is_from_tracker(result):
    """Vérifie si un résultat provient du tracker spécifié."""
    if not TRACKER_DOMAIN:
        return True  # Si aucun domaine n'est spécifié, accepte tous les trackers
    details_url = result.get('Details', '')
    return TRACKER_DOMAIN in urlparse(details_url).netloc

def main():
    """Fonction principale du script."""
    print("Connexion à Jackett")
    session = login_to_jackett()
    if not session:
        return

    print("Récupération du cache Jackett")
    cache_results = get_jackett_cache(session)

    if not cache_results:
        print("Aucun résultat valide trouvé dans le cache Jackett")
        return

    processed_results = []
    for result in cache_results:
        if not (is_movie_or_tv(result) and is_from_tracker(result)):
            continue

        print(f"\nTraitement de: {result['Title']}")
        print(f"Catégorie: {result.get('Category')}")
        print(f"Source: {result.get('Details', 'Inconnue')}")
        print(f"Lien: {result.get('Link', 'Non disponible')}")

        torrent_file_path = download_torrent_file(session, result['Link'])
        
        if torrent_file_path:
            added_to_rd = add_torrent_to_real_debrid(torrent_file_path, result['Title'])
            if added_to_rd:
                print(f"Torrent ajouté avec succès à Real-Debrid: {result['Title']}")
            else:
                print(f"Échec de l'ajout du torrent à Real-Debrid: {result['Title']}")
            os.unlink(torrent_file_path)  # Supprimer le fichier temporaire
        else:
            print("Impossible d'obtenir le fichier .torrent.")
            added_to_rd = False

        processed_result = {
            "title": result["Title"],
            "size": result.get("Size", "Inconnu"),
            "seeders": result.get("Seeders", "Inconnu"),
            "peers": result.get("Peers", "Inconnu"),
            "added_to_rd": "Oui" if added_to_rd else "Non"
        }
        processed_results.append(processed_result)

        print(f"Attente de {WAIT_TIME:.2f} secondes avant le prochain ajout...")
        time.sleep(WAIT_TIME)

    save_to_csv(processed_results, "/data/results.csv")
    print("Traitement du cache Jackett et ajout à Real-Debrid terminés. Résultats sauvegardés dans /data/results.csv")

def run_script():
    """Fonction pour exécuter le script principal avec gestion des erreurs."""
    print("Démarrage du processus CacheFlow...")
    try:
        main()
        print("Processus CacheFlow terminé. En attente de la prochaine exécution.")
    except Exception as e:
        print(f"Une erreur est survenue lors de l'exécution du script: {e}")

if __name__ == "__main__":
    schedule.every(24).hours.do(run_script)
    
    print("Script CacheFlow démarré. S'exécutera toutes les 24 heures.")
    run_script()  # Exécution immédiate au démarrage
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Vérification toutes les minutes
