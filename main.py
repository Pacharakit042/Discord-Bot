# main.py
import discord
from discord.ext import tasks, commands
from discord.ui import View, Button, Select, Modal, InputText
from datetime import datetime, timezone, timedelta
import config, database, pandascore_api

# --- การตั้งค่าและฟังก์ชันสร้าง Embed ---
intents = discord.Intents.default()
bot = discord.Bot(intents=intents)
GAMES_TO_TRACK = ["valorant", "csgo", "lol", "dota2"]
GAME_EMBED_CONFIG = { "valorant": {"name": "Valorant", "color": 0xFD4556}, "csgo": {"name": "CS2", "color": 0xFFA500}, "lol": {"name": "League of Legends", "color": 0x00BFFF}, "dota2": {"name": "Dota 2", "color": 0xFF0000}}

def create_schedule_embed(game_slug: str, time_period: str):
    now = datetime.now(timezone.utc); start_date, end_date, period_str = None, None, ""
    if time_period == "today": start_date = now.replace(hour=0, minute=0, second=0, microsecond=0); end_date = start_date + timedelta(days=1); period_str = "วันนี้"
    elif time_period == "tomorrow": start_date = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0); end_date = start_date + timedelta(days=1); period_str = "วันพรุ่งนี้"
    elif time_period == "this_week": start_date = now.replace(hour=0, minute=0, second=0, microsecond=0); days_until_sunday = 6 - start_date.weekday(); end_date = (start_date + timedelta(days=days_until_sunday)).replace(hour=23, minute=59, second=59); period_str = "สัปดาห์นี้"
    else: return discord.Embed(title="เกิดข้อผิดพลาด", description="ช่วงเวลาไม่ถูกต้อง")
    matches = database.get_matches_for_day(game_slug, start_date.isoformat(), end_date.isoformat())
    config = GAME_EMBED_CONFIG[game_slug]; embed = discord.Embed(title=f"📅 ตารางแข่ง {config['name']} ({period_str})", color=config['color'], timestamp=datetime.now())
    matches_to_display = matches[:7]
    if not matches_to_display: embed.description = f"ไม่พบโปรแกรมการแข่งขันในช่วง{period_str}ครับ"
    else:
        for i, match in enumerate(matches_to_display):
            team1 = match['team1_name']; team2 = match['team2_name']; match_time_utc = datetime.fromisoformat(match['begin_at'].replace('Z', '+00:00'))
            time_str = f"{discord.utils.format_dt(match_time_utc, style='f')} ({discord.utils.format_dt(match_time_utc, style='R')})"
            stream_info = f"📺 [คลิกเพื่อรับชม]({match['stream_url']})" if match['stream_url'] != 'N/A' else "📺 *ยังไม่มีลิงก์*"
            field_value = f"⚔️ **{team1} vs {team2}**\n⏰ {time_str}\n{stream_info}"
            embed.add_field(name=f"🏆 **{match['league_name']}**", value=field_value, inline=False)
            if i < len(matches_to_display) - 1: embed.add_field(name="", value="-"*50, inline=False)
    footer_text = f"แสดง {len(matches_to_display)} จาก {len(matches)} แมตช์ | ข้อมูลจาก Pandascore" if len(matches) > len(matches_to_display) else "ข้อมูลจาก Pandascore"; embed.set_footer(text=footer_text)
    return embed

def create_player_schedule_embed(player_data, matches_data):
    player_name = player_data['name']
    embed = discord.Embed(
        title=f"🔍 ผลการค้นหาแมตช์ของ: {player_name}",
        description=f"โปรแกรมการแข่งขันที่กำลังจะมาถึงของ **{player_name}**",
        color=0x7289DA
    )
    if player_data.get('image_url'):
        embed.set_thumbnail(url=player_data['image_url'])

    if not matches_data:
        embed.add_field(name="ไม่พบข้อมูล", value=f"ไม่พบโปรแกรมการแข่งขันของ **{player_name}** ในเร็วๆ นี้ครับ", inline=False)
    else:
        for match in matches_data:
            team1 = match['opponents'][0]['opponent']['name'] if len(match['opponents']) > 0 else "TBD"
            team2 = match['opponents'][1]['opponent']['name'] if len(match['opponents']) > 1 else "TBD"

            match_time_utc = datetime.fromisoformat(match['begin_at'].replace('Z', '+00:00'))
            time_str = f"{discord.utils.format_dt(match_time_utc, style='f')} ({discord.utils.format_dt(match_time_utc, style='R')})"
            
            stream_url = "N/A"
            if match.get('streams_list'):
                for stream in match['streams_list']:
                    if 'twitch' in stream.get('raw_url', ''): stream_url = stream['raw_url']; break
            stream_info = f"📺 [คลิกเพื่อรับชม]({stream_url})" if stream_url != 'N/A' else "📺 *ยังไม่มีลิงก์*"

            field_value = f"⚔️ **{team1} vs {team2}**\n⏰ {time_str}\n{stream_info}"
            embed.add_field(name=f"🏆 **{match['league']['name']}**", value=field_value, inline=False)
            embed.add_field(name="", value="-"*50, inline=False)

    embed.set_footer(text=f"ข้อมูล ณ วันที่ {datetime.now().strftime('%d/%m/%Y')}")
    return embed

def create_team_schedule_embed(team_data, matches_data):
    team_name = team_data['name']
    embed = discord.Embed(
        title=f"🔍 ผลการค้นหาแมตช์ของทีม: {team_name}",
        description=f"โปรแกรมการแข่งขันที่กำลังจะมาถึงของทีม **{team_name}**",
        color=0x99AAB5 # Discord Grayple
    )
    if team_data.get('image_url'):
        embed.set_thumbnail(url=team_data['image_url'])

    if not matches_data:
        embed.add_field(name="ไม่พบข้อมูล", value=f"ไม่พบโปรแกรมการแข่งขันของทีม **{team_name}** ในเร็วๆ นี้ครับ", inline=False)
    else:
        for match in matches_data:
            team1 = match['opponents'][0]['opponent']['name'] if len(match['opponents']) > 0 else "TBD"
            team2 = match['opponents'][1]['opponent']['name'] if len(match['opponents']) > 1 else "TBD"

            match_time_utc = datetime.fromisoformat(match['begin_at'].replace('Z', '+00:00'))
            time_str = f"{discord.utils.format_dt(match_time_utc, style='f')} ({discord.utils.format_dt(match_time_utc, style='R')})"
            stream_url = next((s['raw_url'] for s in match.get('streams_list', []) if 'twitch' in s.get('raw_url', '')), "N/A")
            stream_info = f"📺 [คลิกเพื่อรับชม]({stream_url})" if stream_url != "N/A" else "📺 *ยังไม่มีลิงก์*"
            field_value = f"⚔️ **{team1} vs {team2}**\n⏰ {time_str}\n{stream_info}"
            embed.add_field(name=f"🏆 **{match['league']['name']}**", value=field_value, inline=False)
            embed.add_field(name="", value="-"*50, inline=False)

    embed.set_footer(text=f"ข้อมูล ณ วันที่ {datetime.now().strftime('%d/%m/%Y')}")
    return embed


# --- UI Components สำหรับ "เลือก" ผลการค้นหา ---

# 1. เมนูเลือกนักแข่ง
class PlayerSelect(Select):
    def __init__(self, players: list):
        # เก็บข้อมูลดิบไว้ใน dict เพื่อให้ callback เรียกใช้ง่าย
        self.players_data = {str(p['id']): p for p in players}
        options = [
            discord.SelectOption(
                label=p['name'], 
                value=str(p['id']), 
                description=f"ทีม: {p.get('current_team', {}).get('name', 'N/A')}"
            ) for p in players[:25] # จำกัดแค่ 25 ตัวเลือก (สูงสุดของ Select)
        ]
        super().__init__(placeholder="เลือกนักแข่งที่ถูกต้อง...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        player_data = self.players_data[self.values[0]]
        
        if not player_data.get('current_team'):
            await interaction.followup.send(f"**{player_data['name']}** ไม่ได้สังกัดทีมในขณะนี้", ephemeral=True)
            return
            
        team_id = player_data['current_team']['id']
        matches = pandascore_api.fetch_team_upcoming_matches(team_id)
        response_embed = create_player_schedule_embed(player_data, matches)
        await interaction.edit_original_response(content=None, embed=response_embed, view=None)

class PlayerSelectView(View):
    def __init__(self, players: list, *, timeout=180):
        super().__init__(timeout=timeout)
        self.add_item(PlayerSelect(players))

# 2. เมนูเลือกทีม
class TeamSelect(Select):
    def __init__(self, teams: list):
        self.teams_data = {str(t['id']): t for t in teams}
        options = [
            discord.SelectOption(
                label=t['name'], 
                value=str(t['id']), 
                description=f"Acronym: {t.get('acronym', 'N/A')}"
            ) for t in teams[:25]
        ]
        super().__init__(placeholder="เลือกทีมที่ถูกต้อง...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        team_data = self.teams_data[self.values[0]]
        
        matches = pandascore_api.fetch_team_upcoming_matches(team_data['id'])
        response_embed = create_team_schedule_embed(team_data, matches)
        await interaction.edit_original_response(content=None, embed=response_embed, view=None)

class TeamSelectView(View):
    def __init__(self, teams: list, *, timeout=180):
        super().__init__(timeout=timeout)
        self.add_item(TeamSelect(teams))


# --- UI Components เดิม ---

# 1. Modals (Pop-ups)
class PlayerSearchModal(Modal):
    def __init__(self, game_slug: str):
        super().__init__(title=f"ค้นหานักแข่งใน {GAME_EMBED_CONFIG[game_slug]['name']}")
        self.game_slug = game_slug; self.add_item(InputText(label="ชื่อนักแข่ง (In-game name)", placeholder="เช่น TenZ, f0rsakeN, s1mple", required=True))

    async def callback(self, interaction: discord.Interaction):
        player_name = self.children[0].value
        await interaction.response.defer(ephemeral=True)
        
        players_found = pandascore_api.search_players(self.game_slug, player_name)
        if not players_found:
            await interaction.followup.send(f"ไม่พบนักแข่งชื่อ '{player_name}'", ephemeral=True)
            return
        await interaction.followup.send("ผลการค้นหา:", view=PlayerSelectView(players_found), ephemeral=True)


class TeamSearchModal(Modal):
    def __init__(self, game_slug: str):
        super().__init__(title=f"ค้นหาทีมใน {GAME_EMBED_CONFIG[game_slug]['name']}")
        self.game_slug = game_slug; self.add_item(InputText(label="ชื่อทีม", placeholder="เช่น Paper Rex, Fnatic, T1", required=True))

    async def callback(self, interaction: discord.Interaction):
        team_name = self.children[0].value
        await interaction.response.defer(ephemeral=True)
        
        teams_found = pandascore_api.search_teams(self.game_slug, team_name)
        if not teams_found:
            await interaction.followup.send(f"ไม่พบทีมชื่อ '{team_name}'", ephemeral=True)
            return   
        await interaction.followup.send("ผลการค้นหา:", view=TeamSelectView(teams_found), ephemeral=True)


# 2. เมนูเลือกเกม
class GameSelect(Select):
    def __init__(self, action: str, time_period: str = None):
        self.action = action; self.time_period = time_period
        options = [discord.SelectOption(label=c["name"], value=s, emoji="🎮") for s, c in GAME_EMBED_CONFIG.items()]
        super().__init__(placeholder=f"กรุณาเลือกเกม...", options=options)

    async def callback(self, interaction: discord.Interaction):
        game_slug = self.values[0]
        if self.action == "schedule":
            response_embed = create_schedule_embed(game_slug, self.time_period)
            await interaction.response.edit_message(content=None, embed=response_embed, view=None)
        elif self.action == "search_player":
            await interaction.response.send_modal(PlayerSearchModal(game_slug))
        elif self.action == "search_team":
            await interaction.response.send_modal(TeamSearchModal(game_slug))


class GameSelectView(View):
    def __init__(self, action: str, time_period: str = None, *, timeout=180):
        super().__init__(timeout=timeout); self.add_item(GameSelect(action, time_period))
class TimePeriodSelectView(View):
    def __init__(self, *, timeout=180): super().__init__(timeout=timeout)
    async def send_game_select(self, i, p): await i.response.edit_message(content="ยอดเยี่ยม! ต่อไปเลือกเกมได้เลย", view=GameSelectView("schedule", p))
    @discord.ui.button(label="วันนี้", style=discord.ButtonStyle.green, emoji="📅")
    async def today(self, b, i): await self.send_game_select(i, "today")
    @discord.ui.button(label="พรุ่งนี้", style=discord.ButtonStyle.primary, emoji="➡️")
    async def tomorrow(self, b, i): await self.send_game_select(i, "tomorrow")
    @discord.ui.button(label="อาทิตย์นี้", style=discord.ButtonStyle.secondary, emoji="🗓️")
    async def this_week(self, b, i): await self.send_game_select(i, "this_week")

# 3. View หลักของแผงควบคุม
class MainControlPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="ดูตารางแข่ง", style=discord.ButtonStyle.green, custom_id="persistent_view:schedule", emoji="📅")
    async def schedule_button(self, b, i): await i.response.send_message(content="เลือกช่วงเวลาที่ต้องการ", view=TimePeriodSelectView(), ephemeral=True)
    @discord.ui.button(label="ค้นหานักแข่ง", style=discord.ButtonStyle.primary, custom_id="persistent_view:search_player", emoji="🔍")
    async def search_player_button(self, b, i): await i.response.send_message(view=GameSelectView(action="search_player"), ephemeral=True)
    @discord.ui.button(label="ค้นหาทีม", style=discord.ButtonStyle.secondary, custom_id="persistent_view:search_team", emoji="👥")
    async def search_team_button(self, b, i): await i.response.send_message(view=GameSelectView(action="search_team"), ephemeral=True)

# --- Event, Task, และคำสั่ง /setup ---
@bot.event
async def on_ready(): bot.add_view(MainControlPanelView()); print(f"✅ บอท {bot.user} ออนไลน์แล้ว!"); database.initialize_db(); update_matches_cache.start()
@tasks.loop(minutes=15)
async def update_matches_cache():
    print(f"[{datetime.now()}] 🔄 Starting background task...");
    for game_slug in GAMES_TO_TRACK:
        matches_data = pandascore_api.fetch_upcoming_matches(game_slug);
        if matches_data: database.upsert_matches(matches_data)
    print("✅ Background task finished.")
@bot.slash_command(name="setup", description="[Admin] สร้างแผงควบคุมในช่องนี้")
@commands.has_permissions(administrator=True)
async def setup_panel(ctx: discord.ApplicationContext):
    await ctx.respond("กำลังสร้าง...", ephemeral=True);
    embed = discord.Embed(
        title="Esports Schedule Bot",
        description=(
            "บอทสำหรับติดตามข่าวสารและตารางการแข่งขัน Esports (Valorant, CS2, LoL, Dota2)\n\n"
            "**วิธีใช้งาน:**\n"
            "🔹 **ดูตารางแข่ง:** กดปุ่ม `ดูตารางแข่ง` แล้วเลือกช่วงเวลาและเกม\n"
            "🔹 **ค้นหานักแข่ง:** กดปุ่ม `ค้นหานักแข่ง` เพื่อดูตารางแข่งของนักแข่งต้องการ\n"
            "🔹 **ค้นหาทีม:** กดปุ่ม `ค้นหาทีม` เพื่อดูตารางแข่งของทีมที่เลือก\n\n"
        ), color=0x2ECC71);
    embed.set_footer(text="กดปุ่มด้านล่างเพื่อเริ่มใช้งาน");
    await ctx.channel.send(embed=embed, view=MainControlPanelView());
    await ctx.edit(content="✅ สร้างแผงควบคุมเรียบร้อยแล้ว!")

# --- รันบอท ---
bot.run(config.DISCORD_BOT_TOKEN)