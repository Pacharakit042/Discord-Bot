# database.py (เวอร์ชันอัปเกรดสำหรับติดตามนักแข่ง)
import sqlite3

DATABASE_FILE = "matches.db"

def initialize_db():
    """สร้างตารางในฐานข้อมูลหากยังไม่มี"""
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        # ตารางเดิม (matches, guild_settings)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id INTEGER PRIMARY KEY, game_slug TEXT NOT NULL, league_name TEXT,
            tournament_name TEXT, team1_name TEXT, team2_name TEXT,
            begin_at TEXT NOT NULL, stream_url TEXT
        )""")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY, dedicated_channel_id INTEGER NOT NULL
        )""")

        # --- ตารางสำหรับนักแข่งและผู้ติดตาม ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT,
            image_url TEXT
        )""")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            UNIQUE(user_id, player_id)
        )""")
        conn.commit()
    print("Database initialized successfully with player tables.")

# --- ฟังก์ชันสำหรับ matches และ guild_settings ---
def get_matches_for_day(game_slug, start_of_day, end_of_day):
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor(); cursor.execute("SELECT * FROM matches WHERE game_slug = ? AND begin_at >= ? AND begin_at < ? ORDER BY begin_at ASC", (game_slug, start_of_day, end_of_day))
        columns = [d[0] for d in cursor.description]; return [dict(zip(columns, r)) for r in cursor.fetchall()]
def upsert_matches(matches_data):
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        for match in matches_data:
            team1 = match['opponents'][0]['opponent']['name'] if match.get('opponents') and len(match['opponents']) > 0 else 'TBD'
            team2 = match['opponents'][1]['opponent']['name'] if match.get('opponents') and len(match['opponents']) > 1 else 'TBD'
            stream_url = "N/A"
            if match.get('streams_list'):
                for stream in match['streams_list']:
                    if 'twitch' in stream.get('raw_url', ''): stream_url = stream['raw_url']; break
            cursor.execute("INSERT OR IGNORE INTO matches (match_id, game_slug, league_name, tournament_name, team1_name, team2_name, begin_at, stream_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (match['id'], match['videogame']['slug'], match['league']['name'], match['tournament']['name'], team1, team2, match['begin_at'], stream_url))
        conn.commit()
def set_dedicated_channel(gid, cid):
    with sqlite3.connect(DATABASE_FILE) as conn: conn.cursor().execute("INSERT OR REPLACE INTO guild_settings (guild_id, dedicated_channel_id) VALUES (?, ?)", (gid, cid)); conn.commit()
def get_dedicated_channel(gid):
    with sqlite3.connect(DATABASE_FILE) as conn:
        res = conn.cursor().execute("SELECT dedicated_channel_id FROM guild_settings WHERE guild_id = ?", (gid,)).fetchone(); return res[0] if res else None

# --- ฟังก์ชันสำหรับจัดการนักแข่งและผู้ติดตาม ---

def add_player_subscription(user_id: int, player_id: int):
    """เพิ่มการติดตามนักแข่งสำหรับผู้ใช้"""
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO player_subscriptions (user_id, player_id) VALUES (?, ?)", (user_id, player_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError: # กรณีที่ติดตามซ้ำ
            return False

def upsert_player(player_data):
    """เพิ่มหรืออัปเดตข้อมูลนักแข่งในแคช"""
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO players (player_id, name, slug, image_url) VALUES (?, ?, ?, ?)",
                       (player_data['id'], player_data['name'], player_data.get('slug'), player_data.get('image_url')))
        conn.commit()