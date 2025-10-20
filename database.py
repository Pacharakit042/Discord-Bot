# database.py
import sqlite3

DATABASE_FILE = "matches.db"

def initialize_db():
    """สร้างตารางในฐานข้อมูลหากยังไม่มี"""
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # ตารางสำหรับแคชข้อมูลแมตช์
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id INTEGER PRIMARY KEY,
            game_slug TEXT NOT NULL,
            league_name TEXT,
            tournament_name TEXT,
            team1_name TEXT,
            team2_name TEXT,
            begin_at TEXT NOT NULL,
            stream_url TEXT
        )
        """)
        
        # ตารางสำหรับเก็บการตั้งค่าของแต่ละเซิร์ฟเวอร์
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,
            dedicated_channel_id INTEGER NOT NULL
        )
        """)
        
        conn.commit()
    print("Database (Cleaned) initialized successfully.")

def upsert_matches(matches_data):

    # อัปเดตหรือเพิ่มข้อมูลแมตช์ลงในฐานข้อมูลแคช

    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        for match in matches_data:
            team1 = match['opponents'][0]['opponent']['name'] if match.get('opponents') and len(match['opponents']) > 0 else 'TBD'
            team2 = match['opponents'][1]['opponent']['name'] if match.get('opponents') and len(match['opponents']) > 1 else 'TBD'
            
            stream_url = "N/A"
            if match.get('streams_list'):
                for stream in match['streams_list']:
                    if 'twitch' in stream.get('raw_url', ''):
                        stream_url = stream['raw_url']
                        break

            cursor.execute("""
            INSERT OR IGNORE INTO matches (
                match_id, game_slug, league_name, tournament_name, 
                team1_name, team2_name, begin_at, stream_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match['id'],
                match['videogame']['slug'],
                match['league']['name'],
                match['tournament']['name'],
                team1,
                team2,
                match['begin_at'],
                stream_url
            ))
        conn.commit()

def get_matches_for_day(game_slug, start_of_day, end_of_day):

    # ดึงข้อมูลแมตช์ของเกมที่ระบุในวันที่กำหนดจากฐานข้อมูลแคช

    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM matches 
        WHERE game_slug = ? AND begin_at >= ? AND begin_at < ?
        ORDER BY begin_at ASC
        """, (game_slug, start_of_day, end_of_day))
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def set_dedicated_channel(guild_id: int, channel_id: int):

    # บันทึกหรืออัปเดตช่องแชทสำหรับเซิร์ฟเวอร์ที่ระบุ

    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO guild_settings (guild_id, dedicated_channel_id) VALUES (?, ?)", (guild_id, channel_id))
        conn.commit()

def get_dedicated_channel(guild_id: int):

    # ดึง ID ของช่องแชทที่เซิร์ฟเวอร์นั้นๆ ตั้งค่าไว้

    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT dedicated_channel_id FROM guild_settings WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        return result[0] if result else None
