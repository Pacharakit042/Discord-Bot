import requests
from config import PANDASCORE_API_TOKEN

BASE_URL = "https://api.pandascore.co"

def fetch_upcoming_matches(game_slug):

    #ดึงข้อมูลแมตช์ที่กำลังจะมาถึงของเกมที่ระบุ

    endpoint = f"/{game_slug}/matches/upcoming"
    params = {
        "token": PANDASCORE_API_TOKEN,
        "sort": "begin_at",
        "per_page": 100
    }
    try:
        response = requests.get(BASE_URL + endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {game_slug}: {e}")
        return []

def search_players(game_slug: str, search_term: str):
    """ค้นหานักแข่งจากชื่อในเกมที่ระบุ"""
    endpoint = f"/{game_slug}/players"
    params = {
        "token": PANDASCORE_API_TOKEN,
        "search[name]": search_term,
        "page[size]": 10 # ค้นหาไม่เกิน 10 คน
    }
    
    try:
        response = requests.get(BASE_URL + endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error searching players for {game_slug}: {e}")
        return []
    
def fetch_team_upcoming_matches(team_id: int):
    """ดึงข้อมูลแมตช์ที่กำลังจะมาถึงของทีมที่ระบุ"""
    endpoint = "/matches/upcoming"
    params = {
        "token": PANDASCORE_API_TOKEN,
        "filter[opponent_id]": team_id,
        "sort": "begin_at",
        "per_page": 5 # ค้นหาแค่ 5 แมตช์ล่าสุด
    }
    
    try:
        response = requests.get(BASE_URL + endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching team matches for team_id {team_id}: {e}")
        return []

def search_teams(game_slug: str, search_term: str):
    """ค้นหาทีมจากชื่อในเกมที่ระบุ"""
    endpoint = f"/{game_slug}/teams"
    params = {
        "token": PANDASCORE_API_TOKEN,
        "search[name]": search_term,
        "page[size]": 10 # ค้นหาไม่เกิน 10 ทีม
    }
    
    try:
        response = requests.get(BASE_URL + endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error searching teams for {game_slug}: {e}")
        return []