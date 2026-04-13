import discord
from discord.ext import commands
from discord import app_commands
import json, os, random, time, asyncio

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_FILE = "arf_fish_v10.json"

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

# ---------- ITEM EFFECTS ----------
def apply_items(u, gain):
    gain += u["treat_upgrade"]
    if u["treat_magnet"] > 0:
        gain *= 2
        u["treat_magnet"] -= 1
    return max(gain, 1)

# ---------- ACTIONS ----------
async def treat_action(i):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)

    if time.time() - u["last_treat"] < 10:
        return "⏱️ wait…"

    u["last_treat"] = time.time()

    gain = apply_items(u, random.randint(5,10))
    xp = gain * (2 if time.time() < u["xp_boost_until"] else 1)

    u["treats"] += gain
    u["xp"] += xp
    u["level"] = u["xp"] // 100

    save_data(d)
    return f"+{gain} treats 🦴 (+{xp} xp)"

async def beg_action(i):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)

    if time.time() - u["last_beg"] < 60:
        return "too soon…"

    u["last_beg"] = time.time()
    gain = random.randint(10,25)
    u["treats"] += gain
    save_data(d)

    return f"*puppy eyes* +{gain}"

async def work_action(i):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)

    if time.time() - u["last_work"] < 120:
        return "too tired…"

    u["last_work"] = time.time()
    gain = random.randint(20,40)
    u["treats"] += gain
    save_data(d)

    return f"+{gain} 💼"

# ---------- UI ----------
class ActionView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid

    async def interaction_check(self, i):
        return i.user.id == self.uid

    @discord.ui.button(label="Treat 🦴", style=discord.ButtonStyle.primary)
    async def treat_btn(self, i, b):
        await i.response.edit_message(content=await treat_action(i), view=self)

    @discord.ui.button(label="Beg 🐶", style=discord.ButtonStyle.secondary)
    async def beg_btn(self, i, b):
        await i.response.edit_message(content=await beg_action(i), view=self)

    @discord.ui.button(label="Work 💼", style=discord.ButtonStyle.success)
    async def work_btn(self, i, b):
        await i.response.edit_message(content=await work_action(i), view=self)

# ---------- COMMANDS ----------
@tree.command(name="treat", description="Main panel 🐾")
async def treat(i: discord.Interaction):
    await safe_send(i, content=await treat_action(i), view=ActionView(i.user.id))

@tree.command(name="beg", description="Beg 🐶")
async def beg(i: discord.Interaction):
    await safe_send(i, content=await beg_action(i))

@tree.command(name="work", description="Work 💼")
async def work(i: discord.Interaction):
    await safe_send(i, content=await work_action(i))

@tree.command(name="daily", description="Daily 🎁")
async def daily(i: discord.Interaction):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)

    if time.time() - u["last_daily"] < 86400:
        return await safe_send(i, content="come back later")

    u["last_daily"] = time.time()
    reward = 50 + (u["streak"] * 5)

    if u["double_daily"]:
        reward *= 2
        u["double_daily"] = False

    u["treats"] += reward
    u["streak"] += 1
    save_data(d)

    await safe_send(i, content=f"+{reward} treats")

# ---------- COINFLIP ----------
@tree.command(name="coinflip", description="Flip a coin 🪙")
async def coinflip(i: discord.Interaction, bet: int, choice: str):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)

    choice = choice.lower()

    if bet <= 0 or bet > u["treats"]:
        return await safe_send(i, content="invalid bet")

    if choice not in ["heads", "tails"]:
        return await safe_send(i, content="choose heads/tails")

    result = random.choice(["heads","tails"])

    if result == choice:
        u["treats"] += bet
        msg = f"🪙 {result} — WON +{bet}"
    else:
        u["treats"] -= bet
        msg = f"🪙 {result} — lost -{bet}"

    save_data(d)
    await safe_send(i, content=msg)

# ---------- SHOP ----------
@tree.command(name="shop", description="Treat shop 🦴")
async def shop(i: discord.Interaction):
    embed = discord.Embed(title="🦴 treat shop 🦴", color=0xF4A261)

    embed.add_field(name="Treat Magnet 🧲 — 20", value="double next treat\n`/buy treat_magnet`", inline=False)
    embed.add_field(name="Lucky Paw 🍀 — 25", value="flavor item\n`/buy lucky_paw`", inline=False)
    embed.add_field(name="Double Daily 📅 — 30", value="double next daily\n`/buy double_daily`", inline=False)
    embed.add_field(name="XP Boost ⚡ — 30", value="2x xp (5 min)\n`/buy xp_boost`", inline=False)
    embed.add_field(name="Big XP Pack 🌟 — 40", value="+200 xp\n`/buy big_xp_pack`", inline=False)
    embed.add_field(name="Treat Upgrade 🦴+ — 20", value="permanent +1\n`/buy treat_upgrade`", inline=False)

    await safe_send(i, embed=embed)

# ---------- BUY ----------
@tree.command(name="buy", description="Buy item")
async def buy(i: discord.Interaction, item: str):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)

    prices = {
        "treat_magnet":20,
        "lucky_paw":25,
        "double_daily":30,
        "xp_boost":30,
        "big_xp_pack":40,
        "treat_upgrade":20
    }

    item = item.lower()

    if item not in prices or u["treats"] < prices[item]:
        return await safe_send(i, content="invalid or not enough")

    u["treats"] -= prices[item]

    if item == "treat_magnet":
        u["treat_magnet"] = 1
    elif item == "double_daily":
        u["double_daily"] = True
    elif item == "xp_boost":
        u["xp_boost_until"] = time.time() + 300
    elif item == "big_xp_pack":
        u["xp"] += 200
    elif item == "treat_upgrade":
        u["treat_upgrade"] += 1

    save_data(d)
    await safe_send(i, content=f"bought {item}")

# ---------- RP ----------
@tree.command(name="hug")
async def hug(i: discord.Interaction, member: discord.Member=None):
    target = member or i.user
    embed = discord.Embed(description=f"{i.user.mention} hugs {target.mention}")
    embed.set_image(url=random.choice(HUG_GIFS))
    await safe_send(i, embed=embed)

@tree.command(name="pat")
async def pat(i: discord.Interaction, member: discord.Member=None):
    target = member or i.user
    embed = discord.Embed(description=f"{i.user.mention} pats {target.mention}")
    embed.set_image(url=random.choice(PAT_GIFS))
    await safe_send(i, embed=embed)

@tree.command(name="cuddle")
async def cuddle(i: discord.Interaction, member: discord.Member=None):
    target = member or i.user
    embed = discord.Embed(description=f"{i.user.mention} cuddles {target.mention}")
    embed.set_image(url=random.choice(CUDDLE_GIFS))
    await safe_send(i, embed=embed)

# ---------- GLOBAL SYNC ----------
@bot.event
async def on_ready():
    print("\n🔥 ===== V10 GLOBAL SYNC =====")

    try:
        tree.clear_commands(guild=None)
        await tree.sync()
        print("🧹 Cleared old commands")

        await asyncio.sleep(2)

        synced = await tree.sync()
        print(f"🌍 Synced {len(synced)} commands")

        print("\n📜 Commands:")
        for cmd in synced:
            print(f" - {cmd.name}")

    except Exception as e:
        print("❌ Sync error:", e)

    print("\n🚀 BOT READY\n")

bot.run(TOKEN)
