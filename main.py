import discord
from discord.ext import commands
from discord import app_commands
import json, os, random, time

TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_FILE = "data.json"

# ---------------- DATA ----------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user(data, guild_id, user_id):
    gid = str(guild_id) if guild_id else "global"
    uid = str(user_id)

    data.setdefault(gid, {})
    data[gid].setdefault(uid, {
        "xp": 0,
        "level": 0,
        "treats": 100,
        "last_treat": 0,
        "last_beg": 0,
        "last_work": 0,
        "treat_upgrade": 0,
        "achievements": [],
        "mood": "neutral",
        "last_mood_change": 0
    })

    return data[gid][uid]

# ---------------- MOOD ----------------
MOODS = ["happy", "neutral", "grumpy", "playful"]

def update_mood(user):
    now = time.time()
    if now - user["last_mood_change"] > 120:
        user["mood"] = random.choice(MOODS)
        user["last_mood_change"] = now

def mood_bonus(user):
    if user["mood"] == "happy": return 2
    if user["mood"] == "grumpy": return -1
    return 0

def mood_text(user, text):
    m = user["mood"]
    if m == "happy": return text + " 😊"
    if m == "grumpy": return "hmph... " + text
    if m == "playful": return text + " WAN!! 🐶"
    return text

# ---------------- LEVEL ----------------
def xp_for_level(level): return 100 * level

def get_level(xp):
    level = 0
    while xp >= xp_for_level(level + 1):
        xp -= xp_for_level(level + 1)
        level += 1
    return level

# ---------------- ACHIEVEMENTS ----------------
ACHIEVEMENTS = {
    "rich": "💰 Reached 1000 treats!",
    "level5": "📈 Reached level 5!"
}

def check_achievements(user):
    unlocked = []

    if user["treats"] >= 1000 and "rich" not in user["achievements"]:
        user["achievements"].append("rich")
        unlocked.append("rich")

    if user["level"] >= 5 and "level5" not in user["achievements"]:
        user["achievements"].append("level5")
        unlocked.append("level5")

    return unlocked

# ---------------- UTIL ----------------
def get_ids(interaction):
    gid = interaction.guild.id if interaction.guild else None
    return gid, interaction.user.id

# ---------------- UI ----------------
class TreatView(discord.ui.View):
    def __init__(self, user_id, user):
        super().__init__(timeout=60)
        self.user_id = user_id

        now = time.time()
        self.treat_btn.disabled = now - user["last_treat"] < 10
        self.beg_btn.disabled = now - user["last_beg"] < 60
        self.work_btn.disabled = now - user["last_work"] < 120

    async def interaction_check(self, interaction):
        return interaction.user.id == self.user_id

    @discord.ui.button(label="Treat 🦴", style=discord.ButtonStyle.primary)
    async def treat_btn(self, interaction, button):
        await handle_treat(interaction)

    @discord.ui.button(label="Beg 🐶", style=discord.ButtonStyle.secondary)
    async def beg_btn(self, interaction, button):
        await handle_beg(interaction)

    @discord.ui.button(label="Work 💼", style=discord.ButtonStyle.success)
    async def work_btn(self, interaction, button):
        await handle_work(interaction)

# ---------------- ACTIONS ----------------
async def handle_treat(interaction):
    data = load_data()
    gid, uid = get_ids(interaction)
    user = get_user(data, gid, uid)

    update_mood(user)

    now = time.time()
    if now - user["last_treat"] < 10:
        return await interaction.response.send_message("⏱️ Slow down!", ephemeral=True)

    user["last_treat"] = now

    gain = max(random.randint(5, 10) + mood_bonus(user), 1)

    user["treats"] += gain
    user["xp"] += gain
    user["level"] = get_level(user["xp"])

    unlocked = check_achievements(user)
    save_data(data)

    msg = mood_text(user, f"You got **{gain} treats** 🦴")

    for a in unlocked:
        msg += f"\n🏆 {ACHIEVEMENTS[a]}"

    await interaction.response.send_message(msg, view=TreatView(uid, user))

async def handle_beg(interaction):
    data = load_data()
    gid, uid = get_ids(interaction)
    user = get_user(data, gid, uid)

    update_mood(user)

    if time.time() - user["last_beg"] < 60:
        return await interaction.response.send_message("⏱️ Too soon!", ephemeral=True)

    user["last_beg"] = time.time()

    gain = max(random.randint(10, 25) + mood_bonus(user), 1)
    user["treats"] += gain

    save_data(data)

    await interaction.response.send_message(
        mood_text(user, f"You begged and got **{gain} treats** 🦴")
    )

async def handle_work(interaction):
    data = load_data()
    gid, uid = get_ids(interaction)
    user = get_user(data, gid, uid)

    update_mood(user)

    if time.time() - user["last_work"] < 120:
        return await interaction.response.send_message("⏱️ Too tired!", ephemeral=True)

    user["last_work"] = time.time()

    job, pay = random.choice([
        ("dug up treasure", 30),
        ("guarded the yard", 25),
        ("fetched items", 20)
    ])

    pay = max(pay + mood_bonus(user), 1)

    user["treats"] += pay
    save_data(data)

    await interaction.response.send_message(
        mood_text(user, f"You {job} and earned **{pay} treats** 🦴")
    )

# ---------------- COMMANDS ----------------
@tree.command(name="treat", description="Get treats 🦴")
@app_commands.allowed_contexts(guilds=True, dms=True)
async def treat(interaction: discord.Interaction):
    await handle_treat(interaction)

@tree.command(name="beg", description="Beg for treats 🐶")
@app_commands.allowed_contexts(guilds=True, dms=True)
async def beg(interaction: discord.Interaction):
    await handle_beg(interaction)

@tree.command(name="work", description="Work for treats 💼")
@app_commands.allowed_contexts(guilds=True, dms=True)
async def work(interaction: discord.Interaction):
    await handle_work(interaction)

# ---------------- RP ----------------
async def rp_action(interaction, member, lines, gifs):
    data = load_data()
    gid, uid = get_ids(interaction)
    user = get_user(data, gid, uid)

    update_mood(user)

    if not interaction.guild:
        member = interaction.user

    if member.id == interaction.user.id:
        text = "You did that to yourself… 🐾"
    elif member.id == bot.user.id:
        text = "WAN?! Me?! 💖"
    else:
        text = random.choice(lines).format(
            user=interaction.user.mention,
            target=member.mention
        )

    text = mood_text(user, text)

    reward = random.randint(1, 3)
    user["treats"] += reward

    save_data(data)

    embed = discord.Embed(
        description=text + f"\n\n+{reward} 🦴",
        color=0xFFA500
    )
    embed.set_image(url=random.choice(gifs))

    await interaction.response.send_message(embed=embed)

@tree.command(name="hug", description="Hug someone 🤗")
@app_commands.allowed_contexts(guilds=True, dms=True)
async def hug(interaction: discord.Interaction, member: discord.Member = None):
    await rp_action(
        interaction,
        member,
        ["{user} hugs {target} 🤗", "{user} cuddles {target} 🐶"],
        ["https://media.tenor.com/8Q2R3kUuS8cAAAAC/anime-hug.gif"]
    )

# ---------------- TROLL ----------------
def troll_embed(title, text):
    e = discord.Embed(title=title, description=text, color=0xFFA500)
    e.set_footer(text="🐾 nice try.")
    return e

@tree.command(name="heat", description="...")
@app_commands.allowed_contexts(guilds=True, dms=True)
async def heat(interaction):
    extra = "…why in DMs 😭" if not interaction.guild else ""
    await interaction.response.send_message(
        embed=troll_embed("😳 Heat...", random.choice([
            "zoomies activated", "too wholesome 💀", "bonk"
        ]) + " " + extra)
    )

@tree.command(name="lewd", description="...")
@app_commands.allowed_contexts(guilds=True, dms=True)
async def lewd(interaction):
    await interaction.response.send_message(
        embed=troll_embed("🚫 Lewd Blocked", random.choice([
            "converted to cuddles", "bonk jail", "WAN!! no"
        ]))
    )

@tree.command(name="breed", description="...")
@app_commands.allowed_contexts(guilds=True, dms=True)
async def breed(interaction, member: discord.Member = None):
    target = member.mention if member else interaction.user.mention
    await interaction.response.send_message(
        embed=troll_embed("⚠️ Blocked", f"{target} got tackled with affection 🐶")
    )

# ---------------- HELP ----------------
class HelpView(discord.ui.View):

    @discord.ui.button(label="Economy 🦴", style=discord.ButtonStyle.primary)
    async def eco(self, interaction, button):
        await interaction.response.edit_message(embed=discord.Embed(
            title="🦴 Economy",
            description="/treat /beg /work",
            color=0xFFA500
        ), view=self)

    @discord.ui.button(label="RP 🎭", style=discord.ButtonStyle.secondary)
    async def rp(self, interaction, button):
        await interaction.response.edit_message(embed=discord.Embed(
            title="🎭 RP Commands",
            description="/hug and more",
            color=0xFFA500
        ), view=self)

    @discord.ui.button(label="Mystery 😈", style=discord.ButtonStyle.danger)
    async def mys(self, interaction, button):
        await interaction.response.edit_message(embed=discord.Embed(
            title="😈 Mystery",
            description="/heat /lewd /breed",
            color=0xFFA500
        ), view=self)

@tree.command(name="help", description="View commands 🐶")
@app_commands.allowed_contexts(guilds=True, dms=True)
async def help(interaction):
    embed = discord.Embed(
        title="🐶 arf-fish",
        description="Explore commands using buttons below!",
        color=0xFFA500
    )
    await interaction.response.send_message(embed=embed, view=HelpView())

# ---------------- SYNC FIX ----------------
@bot.event
async def setup_hook():
    try:
        guild = discord.Object(id=1465078377944977595)
        await tree.sync(guild=guild)
        print("Commands synced in setup_hook.")
    except Exception as e:
        print(f"Setup sync error: {e}")

# ---------------- START ----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
