import discord
from discord.ext import commands
from discord import app_commands
import json, os, random, time

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_FILE = "arf_fish_v11.json"

# ---------- SAFE SEND ----------
async def safe_send(i, **kwargs):
    try:
        if not i.response.is_done():
            await i.response.send_message(**kwargs)
        else:
            await i.followup.send(**kwargs)
    except Exception as e:
        print("Send error:", e)

# ---------- DATA ----------
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            return json.load(open(DATA_FILE))
        except:
            return {}
    return {}

def save_data(data):
    json.dump(data, open(DATA_FILE, "w"), indent=2)

def get_user(d, g, u):
    g, u = str(g), str(u)
    d.setdefault(g, {})
    d[g].setdefault(u, {
        "xp":0,"level":0,"treats":100,
        "last_treat":0,"last_beg":0,"last_work":0,"last_daily":0,
        "streak":0,
        "treat_upgrade":0,
        "xp_boost_until":0,
        "treat_magnet":0,
        "double_daily":False
    })
    return d[g][u]

# ---------- GIFS ----------
HUG_GIFS = [
    "https://media.tenor.com/6f7rF0l1R4cAAAAC/anime-hug.gif",
    "https://media.tenor.com/OXCV_qL-V60AAAAC/mochi-peachcat-hug.gif"
]
PAT_GIFS = [
    "https://media.tenor.com/Ws6Dm1ZW_vMAAAAC/pat-head.gif"
]
CUDDLE_GIFS = [
    "https://media.tenor.com/H2X7b7ZQZbQAAAAC/anime-cuddle.gif"
]

# ---------- ACTION ----------
def apply_items(u, gain):
    gain += u["treat_upgrade"]
    if u["treat_magnet"] > 0:
        gain *= 2
        u["treat_magnet"] -= 1
    return max(gain, 1)

async def treat_action(i):
    d = load_data()
    u = get_user(d, i.guild.id, i.user.id)

    if time.time() - u["last_treat"] < 10:
        return "⏱️ wait…"

    u["last_treat"] = time.time()

    gain = apply_items(u, random.randint(5, 10))
    xp = gain * (2 if time.time() < u["xp_boost_until"] else 1)

    u["treats"] += gain
    u["xp"] += xp
    u["level"] = u["xp"] // 100

    save_data(d)
    return f"+{gain} treats 🦴 (+{xp} xp)"

# ---------- COMMANDS ----------
@tree.command(name="treat")
async def treat(i: discord.Interaction):
    await safe_send(i, content=await treat_action(i))

@tree.command(name="beg")
async def beg(i: discord.Interaction):
    await safe_send(i, content="*puppy eyes* +random treats")

@tree.command(name="work")
async def work(i: discord.Interaction):
    await safe_send(i, content="+25 💼")

@tree.command(name="daily")
async def daily(i: discord.Interaction):
    await safe_send(i, content="+50 🎁")

@tree.command(name="coinflip")
async def coinflip(i: discord.Interaction, choice: str):
    result = random.choice(["heads", "tails"])
    await safe_send(i, content=f"🪙 {result}")

@tree.command(name="shop")
async def shop(i: discord.Interaction):
    embed = discord.Embed(title="🦴 treat shop 🦴", color=0xF4A261)
    embed.add_field(name="Treat Magnet 🧲 — 20", value="double next treat", inline=False)
    embed.add_field(name="XP Boost ⚡ — 30", value="2x xp", inline=False)
    await safe_send(i, embed=embed)

@tree.command(name="buy")
async def buy(i: discord.Interaction, item: str):
    await safe_send(i, content=f"bought {item}")

@tree.command(name="hug")
async def hug(i: discord.Interaction):
    embed = discord.Embed(description="hug 🫂")
    embed.set_image(url=random.choice(HUG_GIFS))
    await safe_send(i, embed=embed)

@tree.command(name="pat")
async def pat(i: discord.Interaction):
    embed = discord.Embed(description="pat 🐶")
    embed.set_image(url=random.choice(PAT_GIFS))
    await safe_send(i, embed=embed)

@tree.command(name="cuddle")
async def cuddle(i: discord.Interaction):
    embed = discord.Embed(description="cuddle 💖")
    embed.set_image(url=random.choice(CUDDLE_GIFS))
    await safe_send(i, embed=embed)

# ---------- SAFE SYNC ----------
@bot.event
async def on_ready():
    print("\n🔥 ===== V11 SAFE SYNC =====")

    try:
        local_cmds = [cmd.name for cmd in tree.walk_commands()]
        print(f"📦 Loaded {len(local_cmds)} commands")

        if not local_cmds:
            print("❌ No commands loaded — skipping sync")
            return

        synced = await tree.sync()
        print(f"🌍 Synced {len(synced)} commands")

    except Exception as e:
        print("❌ Sync error:", e)

    print("🚀 READY\n")

bot.run(TOKEN)
