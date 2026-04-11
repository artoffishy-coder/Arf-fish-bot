import discord
from discord.ext import commands
from discord import app_commands
import json, os, random, time

TOKEN = os.getenv("TOKEN")

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
        "inventory": [],
        "last_treat": 0,
        "last_beg": 0,
        "last_work": 0,
        "mood": "neutral",
        "achievements": []
    })

    return data[gid][uid]

def get_ids(interaction):
    gid = interaction.guild.id if interaction.guild else None
    return gid, interaction.user.id

# ---------------- LEVEL ----------------
def xp_for_level(level): return 100 * level

def get_level(xp):
    level = 0
    while xp >= xp_for_level(level + 1):
        xp -= xp_for_level(level + 1)
        level += 1
    return level

# ---------------- MOOD ----------------
MOODS = ["happy", "neutral", "grumpy", "playful"]

def update_mood(user):
    if random.random() < 0.2:
        user["mood"] = random.choice(MOODS)

def mood_bonus(user):
    return 2 if user["mood"] == "happy" else -1 if user["mood"] == "grumpy" else 0

def mood_text(user, text):
    if user["mood"] == "happy": return text + " 😊"
    if user["mood"] == "grumpy": return "hmph… " + text
    if user["mood"] == "playful": return text + " WAN!! 🐶"
    return text

# ---------------- ACHIEVEMENTS ----------------
ACHIEVEMENTS = {
    "rich": "💰 1000 treats!",
    "level5": "📈 Level 5 reached!"
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

# ---------------- SHOP ----------------
SHOP = {
    "xp_boost": {"name": "XP Boost ⚡", "price": 50},
    "lucky": {"name": "Lucky Paw 🍀", "price": 40},
}

# ---------------- UI ----------------
class TreatView(discord.ui.View):
    def __init__(self, uid, user):
        super().__init__(timeout=60)
        self.uid = uid

        now = time.time()
        self.treat_btn.disabled = now - user["last_treat"] < 10
        self.beg_btn.disabled = now - user["last_beg"] < 60
        self.work_btn.disabled = now - user["last_work"] < 120

    async def interaction_check(self, interaction):
        return interaction.user.id == self.uid

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

    if time.time() - user["last_treat"] < 10:
        return await interaction.response.send_message("⏱️ Wait!", ephemeral=True)

    user["last_treat"] = time.time()
    update_mood(user)

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

    if time.time() - user["last_beg"] < 60:
        return await interaction.response.send_message("⏱️ Too soon!", ephemeral=True)

    user["last_beg"] = time.time()
    gain = random.randint(10, 25)

    user["treats"] += gain
    save_data(data)

    await interaction.response.send_message(mood_text(user, f"You got **{gain} treats** 🐶"))

async def handle_work(interaction):
    data = load_data()
    gid, uid = get_ids(interaction)
    user = get_user(data, gid, uid)

    if time.time() - user["last_work"] < 120:
        return await interaction.response.send_message("⏱️ Too tired!", ephemeral=True)

    user["last_work"] = time.time()
    gain = random.randint(20, 40)

    user["treats"] += gain
    save_data(data)

    await interaction.response.send_message(mood_text(user, f"You earned **{gain} treats** 💼"))

# ---------------- COMMANDS ----------------
@tree.command(name="treat", description="Get treats 🦴")
async def treat(interaction: discord.Interaction):
    await handle_treat(interaction)

@tree.command(name="beg", description="Beg for treats 🐶")
async def beg(interaction: discord.Interaction):
    await handle_beg(interaction)

@tree.command(name="work", description="Work for treats 💼")
async def work(interaction: discord.Interaction):
    await handle_work(interaction)

@tree.command(name="inventory")
async def inventory(interaction: discord.Interaction):
    data = load_data()
    user = get_user(data, interaction.guild.id if interaction.guild else None, interaction.user.id)

    items = "\n".join(user["inventory"]) or "Empty"

    embed = discord.Embed(title="🎒 Inventory", description=items, color=0xFFA500)
    await interaction.response.send_message(embed=embed)

@tree.command(name="shop")
async def shop(interaction: discord.Interaction):
    text = "\n".join([f"{v['name']} — {v['price']} treats" for v in SHOP.values()])
    await interaction.response.send_message(embed=discord.Embed(title="🛒 Shop", description=text, color=0xFFA500))

@tree.command(name="buy")
async def buy(interaction: discord.Interaction, item: str):
    data = load_data()
    user = get_user(data, interaction.guild.id if interaction.guild else None, interaction.user.id)

    if item not in SHOP:
        return await interaction.response.send_message("Invalid item")

    if user["treats"] < SHOP[item]["price"]:
        return await interaction.response.send_message("Not enough treats")

    user["treats"] -= SHOP[item]["price"]
    user["inventory"].append(SHOP[item]["name"])
    save_data(data)

    await interaction.response.send_message(f"Bought {SHOP[item]['name']}")

# ---------------- RP ----------------
@tree.command(name="hug")
async def hug(interaction: discord.Interaction, member: discord.Member = None):
    target = member.mention if member else interaction.user.mention

    embed = discord.Embed(
        description=f"{interaction.user.mention} hugs {target} 🤗",
        color=0xFFA500
    )
    embed.set_image(url="https://media.tenor.com/8Q2R3kUuS8cAAAAC/anime-hug.gif")

    await interaction.response.send_message(embed=embed)

# ---------------- HELP ----------------
class HelpView(discord.ui.View):
    @discord.ui.button(label="Economy", style=discord.ButtonStyle.primary)
    async def eco(self, interaction, button):
        await interaction.response.edit_message(content="/treat /beg /work /shop", view=self)

    @discord.ui.button(label="RP", style=discord.ButtonStyle.secondary)
    async def rp(self, interaction, button):
        await interaction.response.edit_message(content="/hug", view=self)

@tree.command(name="help")
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("Use buttons below 👇", view=HelpView())

# ---------------- START ----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} commands globally")
    except Exception as e:
        print(f"❌ Sync error: {e}")

bot.run(TOKEN)
