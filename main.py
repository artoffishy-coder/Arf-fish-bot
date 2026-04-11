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

    if gid not in data:
        data[gid] = {}

    if uid not in data[gid]:
        data[gid][uid] = {
            "xp": 0,
            "level": 0,
            "treats": 100,
            "last_treat": 0,
            "last_beg": 0,
            "last_work": 0,
        }

    return data[gid][uid]

def get_ids(interaction):
    gid = interaction.guild.id if interaction.guild else None
    return gid, interaction.user.id

# -------- COMMANDS --------
@tree.command(name="treat", description="Get treats")
async def treat(interaction: discord.Interaction):
    data = load_data()
    gid, uid = get_ids(interaction)
    user = get_user(data, gid, uid)

    now = time.time()
    if now - user["last_treat"] < 10:
        return await interaction.response.send_message("⏱️ Wait a bit!", ephemeral=True)

    user["last_treat"] = now
    gain = random.randint(5, 10)

    user["treats"] += gain
    user["xp"] += gain

    save_data(data)

    await interaction.response.send_message(f"You got **{gain} treats** 🦴")

@tree.command(name="beg", description="Beg for treats")
async def beg(interaction: discord.Interaction):
    data = load_data()
    gid, uid = get_ids(interaction)
    user = get_user(data, gid, uid)

    if time.time() - user["last_beg"] < 60:
        return await interaction.response.send_message("⏱️ Too soon!", ephemeral=True)

    user["last_beg"] = time.time()
    gain = random.randint(10, 20)

    user["treats"] += gain
    save_data(data)

    await interaction.response.send_message(f"You got **{gain} treats** 🐶")

@tree.command(name="work", description="Work for treats")
async def work(interaction: discord.Interaction):
    data = load_data()
    gid, uid = get_ids(interaction)
    user = get_user(data, gid, uid)

    if time.time() - user["last_work"] < 120:
        return await interaction.response.send_message("⏱️ Too tired!", ephemeral=True)

    user["last_work"] = time.time()
    gain = random.randint(20, 30)

    user["treats"] += gain
    save_data(data)

    await interaction.response.send_message(f"You earned **{gain} treats** 💼")

@tree.command(name="hug", description="Hug someone")
async def hug(interaction: discord.Interaction, member: discord.Member = None):
    target = member.mention if member else interaction.user.mention
    await interaction.response.send_message(f"{interaction.user.mention} hugs {target} 🤗")

# -------- SYNC FIX --------
@bot.event
async def setup_hook():
    guild = discord.Object(id=1465078377944977595)

    tree.clear_commands(guild=guild)
    await tree.sync(guild=guild)

    print("Commands synced.")

# -------- START --------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
