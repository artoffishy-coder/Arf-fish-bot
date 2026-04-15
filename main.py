import discord
from discord import app_commands
from discord.ext import commands
import json, random, time, os, asyncio

# ======================
# ⚙️ CONFIG
# ======================

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ TOKEN NOT FOUND")
    exit()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_FILE = "arf_fish_v18.json"

# ======================
# 🧠 DATA SYSTEM
# ======================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user(data, gid, uid):
    gid, uid = str(gid), str(uid)

    if gid not in data:
        data[gid] = {}

    if uid not in data[gid]:
        data[gid][uid] = {
            "treats": 0,
            "bond": 0,
            "last_interaction": 0,
            "is_favorite": False,
            "memory": [],
            "magnet": False,
            "lucky": False,
            "upgrade": 0,
            "daily_boost": False
        }

    return data[gid][uid]

# ======================
# 💖 OBSESSION
# ======================

def update_obsession(data, gid):
    users = data.get(str(gid), {})
    if not users:
        return

    top = max(users.items(), key=lambda x: x[1]["bond"])[0]

    for uid in users:
        users[uid]["is_favorite"] = (uid == top)

def update_user(data, gid, u, trigger=None):
    now = time.time()

    if now - u["last_interaction"] > 3600:
        u["bond"] = max(0, u["bond"] - 1)

    u["bond"] += 1
    u["last_interaction"] = now

    if trigger:
        if len(u["memory"]) > 6:
            u["memory"].pop(0)
        u["memory"].append(trigger)

    update_obsession(data, gid)

# ======================
# ⏱ THINKING
# ======================

async def think():
    await asyncio.sleep(random.uniform(0.3, 0.8))

# ======================
# 🛠 SAFE SEND
# ======================

async def send(i, msg=None, embed=None, view=None):
    await think()

    if not i.response.is_done():
        await i.response.send_message(content=msg, embed=embed, view=view)
    else:
        await i.followup.send(content=msg, embed=embed, view=view)

# ======================
# 🎬 GIFS
# ======================

GIFS = {
    "hug": ["https://media.tenor.com/9e1aE7i1kV0AAAAC/anime-hug.gif"],
    "pat": ["https://media.tenor.com/zrq4G5d0F6kAAAAC/headpat-anime.gif"],
    "cuddle": ["https://media.tenor.com/0t7G5v6J6eYAAAAC/anime-cuddle.gif"],
    "boop": ["https://media.tenor.com/5Z1WZz9X6V0AAAAC/anime-boop.gif"],
    "kiss": ["https://media.tenor.com/fO9dXW5G7XQAAAAC/anime-kiss.gif"],
    "bite": ["https://media.tenor.com/X7i6F0b7Y7kAAAAC/anime-bite.gif"],
    "lick": ["https://media.tenor.com/Q7z6K5sZ1mYAAAAC/anime-lick.gif"]
}

def gif(a): return random.choice(GIFS[a])

# ======================
# 🛒 SHOP UI
# ======================

SHOP = {
    "magnet": (20, "Double next treat"),
    "lucky": (25, "Big treat reward"),
    "upgrade": (30, "Permanent +1"),
    "daily": (30, "Double daily"),
    "bond": (50, "+10 bond")
}

class ShopView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    async def interaction_check(self, interaction):
        return interaction.user.id == self.user_id

    async def buy(self, interaction, item):
        data = load_data()
        u = get_user(data, interaction.guild.id, interaction.user.id)

        cost = SHOP[item][0]

        if u["treats"] < cost:
            return await interaction.response.send_message(
                "not enough treats 💀", ephemeral=True
            )

        u["treats"] -= cost

        if item == "magnet": u["magnet"] = True
        elif item == "lucky": u["lucky"] = True
        elif item == "upgrade": u["upgrade"] += 1
        elif item == "daily": u["daily_boost"] = True
        elif item == "bond": u["bond"] += 10

        save_data(data)

        await interaction.response.send_message(
            f"bought **{item}** 🐾", ephemeral=True
        )

    @discord.ui.button(label="🧲 Magnet", style=discord.ButtonStyle.primary)
    async def magnet(self, i, b): await self.buy(i, "magnet")

    @discord.ui.button(label="🍀 Lucky", style=discord.ButtonStyle.success)
    async def lucky(self, i, b): await self.buy(i, "lucky")

    @discord.ui.button(label="⚡ Boost", style=discord.ButtonStyle.secondary)
    async def boost(self, i, b): await self.buy(i, "upgrade")

    @discord.ui.button(label="📅 Daily", style=discord.ButtonStyle.secondary)
    async def daily(self, i, b): await self.buy(i, "daily")

    @discord.ui.button(label="💖 Bond", style=discord.ButtonStyle.danger)
    async def bond(self, i, b): await self.buy(i, "bond")

@tree.command(name="shop", description="open the shop 🐾")
async def shop(i):
    embed = discord.Embed(
        title="🐾 Treat Shop",
        description="click… things… I think?",
        color=0xffb6c1
    )

    for k,(c,d) in SHOP.items():
        embed.add_field(name=f"{k} — {c}", value=d, inline=False)

    embed.set_footer(text="buttons below!!")

    await send(i, embed=embed, view=ShopView(i.user.id))

# ======================
# 🎒 INVENTORY
# ======================

@tree.command(name="inventory", description="check your stuff 🐾")
async def inventory(i):
    data = load_data()
    u = get_user(data, i.guild.id, i.user.id)

    embed = discord.Embed(title="🎒 Inventory", color=0x89CFF0)

    embed.add_field(name="🦴 Treats", value=u["treats"], inline=False)

    effects = []
    if u["magnet"]: effects.append("🧲 Magnet ready")
    if u["lucky"]: effects.append("🍀 Lucky ready")
    if u["daily_boost"]: effects.append("📅 Daily ready")
    if u["upgrade"] > 0: effects.append(f"⚡ +{u['upgrade']} passive")

    if not effects:
        effects.append("nothing 😭")

    embed.add_field(name="✨ Effects", value="\n".join(effects), inline=False)
    embed.add_field(name="💖 Bond", value=u["bond"], inline=False)

    if u["is_favorite"]:
        embed.set_footer(text="you’re the favorite 🐾")

    await send(i, embed=embed)

# ======================
# 🦴 ECONOMY
# ======================

@tree.command(name="treat", description="get treats 🐾")
async def treat(i):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"treat")

    gain=random.randint(5,10)

    if u["magnet"]: gain*=2; u["magnet"]=False
    if u["lucky"]: gain=random.randint(15,25); u["lucky"]=False

    gain+=u["upgrade"]
    u["treats"]+=gain

    save_data(d)
    await send(i, f"+{gain} treats 🐾")

@tree.command(name="daily", description="daily treats 📅")
async def daily(i):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)

    reward=50
    if u["daily_boost"]:
        reward*=2
        u["daily_boost"]=False

    u["treats"]+=reward
    save_data(d)

    await send(i, f"+{reward} treats 🐾")

@tree.command(name="coinflip", description="flip coin 🪙")
async def coinflip(i):
    await send(i, random.choice(["heads","tails"]))

# ======================
# 🎭 RP
# ======================

def rp(action, target, fav):
    lines = {
        "hug":[f"*hugs {target.mention}* don’t move 😭"],
        "pat":[f"*pat pat* good… something"],
        "cuddle":[f"*cuddles* okay wait this is nice 😳"],
        "boop":[f"*boop* hehe"],
        "kiss":[f"*quick kiss* WAIT 😭"],
        "bite":[f"*nom*"],
        "lick":[f"*lick* WAIT 💀"]
    }[action]

    if fav:
        lines.append("mine 🐾")

    return random.choice(lines)

@tree.command(name="hug", description="hug 🐾")
async def hug(i, m: discord.Member):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"hug"); save_data(d)
    await send(i, f"{rp('hug',m,u['is_favorite'])}\n{gif('hug')}")

# ======================
# 💬 PASSIVE
# ======================

@bot.event
async def on_message(msg):
    if msg.author.bot: return

    if "good girl" in msg.content.lower():
        await msg.reply("*tail wagging* WAIT me?? 😳")

    if random.random() < 0.03:
        await msg.reply("…hi")

    await bot.process_commands(msg)

# ======================
# 🚀 READY
# ======================

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ V18 READY: {bot.user}")

bot.run(TOKEN)
