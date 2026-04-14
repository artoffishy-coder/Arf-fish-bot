import discord
from discord import app_commands
from discord.ext import commands
import json, random, time, os, asyncio

# ======================
# ⚙️ BOT SETUP
# ======================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_FILE = "arf_fish_v16_full.json"

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
# 💖 OBSESSION SYSTEM
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
# ⏱ THINKING SYSTEM
# ======================

async def think():
    await asyncio.sleep(random.uniform(0.4, 1.0))

# ======================
# 🛠 SAFE SEND
# ======================

async def send(i, msg):
    await think()

    if not i.response.is_done():
        await i.response.send_message(msg)
    else:
        await i.followup.send(msg)

    # small ADHD extra line
    if random.random() < 0.1:
        await i.followup.send(random.choice([
            "wait—",
            "…hold on",
            "I forgot 😭"
        ]))

# ======================
# 🎬 GIF SYSTEM
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

def get_gif(action):
    return random.choice(GIFS[action])

# ======================
# 🛒 SHOP SYSTEM
# ======================

SHOP = {
    "magnet": (20, "Double next treat"),
    "lucky": (25, "Big treat gain"),
    "upgrade": (30, "Permanent +1 treat"),
    "daily": (30, "Double next daily"),
    "bond": (50, "Increase bond")
}

@tree.command(name="shop", description="look at shiny things 🐾")
async def shop(i: discord.Interaction):
    embed = discord.Embed(title="🐾 Shop", color=0xffb6c1)

    for name, (cost, desc) in SHOP.items():
        embed.add_field(name=f"{name} ({cost})", value=desc, inline=False)

    await i.response.send_message(embed=embed)

@tree.command(name="buy", description="buy something 🐾")
async def buy(i: discord.Interaction, item: str):

    item = item.lower()

    if item not in SHOP:
        return await i.response.send_message("not real 😭")

    d = load_data()
    u = get_user(d, i.guild.id, i.user.id)

    cost = SHOP[item][0]

    if u["treats"] < cost:
        return await i.response.send_message("not enough treats 💀")

    u["treats"] -= cost

    if item == "magnet":
        u["magnet"] = True
    elif item == "lucky":
        u["lucky"] = True
    elif item == "upgrade":
        u["upgrade"] += 1
    elif item == "daily":
        u["daily_boost"] = True
    elif item == "bond":
        u["bond"] += 10

    save_data(d)

    await i.response.send_message(f"bought {item} 🐾")

# ======================
# 🦴 ECONOMY COMMANDS
# ======================

@tree.command(name="treat", description="give treats 🐶")
async def treat(i: discord.Interaction):

    d = load_data()
    u = get_user(d, i.guild.id, i.user.id)

    update_user(d, i.guild.id, u, "treat")

    gain = random.randint(5, 10)

    if u["magnet"]:
        gain *= 2
        u["magnet"] = False

    if u["lucky"]:
        gain = random.randint(15, 25)
        u["lucky"] = False

    gain += u["upgrade"]

    u["treats"] += gain
    save_data(d)

    await send(i, f"+{gain} treats 🐾")

@tree.command(name="daily", description="daily treats 📅")
async def daily(i: discord.Interaction):

    d = load_data()
    u = get_user(d, i.guild.id, i.user.id)

    reward = 50

    if u["daily_boost"]:
        reward *= 2
        u["daily_boost"] = False

    u["treats"] += reward
    save_data(d)

    await send(i, f"+{reward} treats 🐾")

@tree.command(name="coinflip", description="flip coin 🪙")
async def coinflip(i: discord.Interaction):
    await send(i, random.choice(["heads", "tails"]))

# ======================
# 😈 PERSONALITY COMMANDS
# ======================

@tree.command(name="lewd", description="do you mean… food..? 🐶")
async def lewd(i: discord.Interaction):

    d = load_data()
    u = get_user(d, i.guild.id, i.user.id)

    update_user(d, i.guild.id, u, "lewd")
    save_data(d)

    responses = [
        "lewd…? is that food— WAIT are we eating??",
        "should I say yes?? I don’t know what that means 😭",
        "I feel like I just agreed to something",
        "*gets close* what are you asking me to do 😳",
        "wait say it again— no I forgot 💀"
    ]

    if "lewd" in u["memory"]:
        responses.append("…you did that earlier didn’t you")

    await send(i, random.choice(responses))

@tree.command(name="heat", description="oh no… what did you do… 🐾")
async def heat(i: discord.Interaction):
    await send(i, random.choice([
        "WAIT something’s happening 😭",
        "this feels weird",
        "*clings to you* stay"
    ]))

@tree.command(name="nsfw", description="DO NOT THE PUPPYGIRL ❗")
async def nsfw(i: discord.Interaction):
    await send(i, random.choice([
        "you clicked that FAST 💀",
        "*stares at you*",
        "you’re gonna press it again aren’t you"
    ]))

# ======================
# 🎭 RP COMMANDS
# ======================

def rp_line(action, target, fav, jealous):
    base = {
        "hug": [f"*hugs {target.mention}* don’t move 😭"],
        "pat": [f"*pats {target.mention}* good… something"],
        "cuddle": [f"*cuddles {target.mention}* okay this is nice 😳"],
        "boop": [f"*boops {target.mention}* hehe"],
        "kiss": [f"*quick kiss on {target.mention}* WAIT 😭"],
        "bite": [f"*nom {target.mention}* don’t run"],
        "lick": [f"*licks {target.mention}* WAIT I did that 💀"]
    }[action]

    if fav:
        base.append(f"*sticks close to {target.mention}* mine 🐾")

    if jealous:
        base.append("…no. mine.")

    return random.choice(base)

@tree.command(name="hug", description="hug someone 🐾")
async def hug(i, member: discord.Member):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"hug"); save_data(d)

    await send(i, f"{rp_line('hug', member, u['is_favorite'], member!=i.user)}\n{get_gif('hug')}")

@tree.command(name="pat", description="pat someone 🐾")
async def pat(i, member: discord.Member):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"pat"); save_data(d)

    await send(i, f"{rp_line('pat', member, u['is_favorite'], False)}\n{get_gif('pat')}")

@tree.command(name="cuddle", description="cuddle someone 🐾")
async def cuddle(i, member: discord.Member):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"cuddle"); save_data(d)

    await send(i, f"{rp_line('cuddle', member, u['is_favorite'], False)}\n{get_gif('cuddle')}")

@tree.command(name="boop", description="boop someone 🐾")
async def boop(i, member: discord.Member):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"boop"); save_data(d)

    await send(i, f"{rp_line('boop', member, u['is_favorite'], False)}\n{get_gif('boop')}")

@tree.command(name="kiss", description="kiss someone 😳")
async def kiss(i, member: discord.Member):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"kiss"); save_data(d)

    await send(i, f"{rp_line('kiss', member, u['is_favorite'], False)}\n{get_gif('kiss')}")

@tree.command(name="bite", description="playfully bite 🐶")
async def bite(i, member: discord.Member):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"bite"); save_data(d)

    await send(i, f"{rp_line('bite', member, u['is_favorite'], False)}\n{get_gif('bite')}")

@tree.command(name="lick", description="…lick?? 😭")
async def lick(i, member: discord.Member):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"lick"); save_data(d)

    await send(i, f"{rp_line('lick', member, u['is_favorite'], False)}\n{get_gif('lick')}")

# ======================
# 💬 PASSIVE REACTIONS
# ======================

@bot.event
async def on_message(msg):
    if msg.author.bot:
        return

    text = msg.content.lower()

    if "good girl" in text or "good boy" in text:
        await msg.reply(random.choice([
            "*tail wagging FAST* WAIT ME?? 😳",
            "I DID GOOD?? SAY IT AGAIN",
            "*happy noises*"
        ]))

    if "@" in text and random.random() < 0.15:
        await msg.reply("…hey. who’s that")

    if random.random() < 0.03:
        await msg.reply("…hi")

    await bot.process_commands(msg)

# ======================
# 🚀 READY
# ======================

@bot.event
async def on_ready():
    await tree.sync()
    print("V16 FULL READY")

bot.run("YOUR_TOKEN_HERE")
