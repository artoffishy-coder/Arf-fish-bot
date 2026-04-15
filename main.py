import discord
from discord import app_commands
from discord.ext import commands
import json, random, time, os, asyncio

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("NO TOKEN")
    exit()

# SAFE INTENTS
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_FILE = "arf_v20.json"

# ======================
# DATA
# ======================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        return json.load(open(DATA_FILE))
    except:
        return {}

def save_data(d):
    json.dump(d, open(DATA_FILE, "w"), indent=2)

def get_user(d, gid, uid):
    gid, uid = str(gid), str(uid)

    if gid not in d:
        d[gid] = {}

    if uid not in d[gid]:
        d[gid][uid] = {
            "treats":0,
            "bond":0,
            "last":0,
            "favorite":False,
            "memory":[],
            "magnet":False,
            "lucky":False,
            "upgrade":0,
            "daily":False,
            "mood":"happy"
        }

    return d[gid][uid]

# ======================
# MOOD
# ======================

MOODS = ["happy","clingy","jealous","sleepy","chaotic"]

def update_mood(u):
    if random.random() < 0.4:
        u["mood"] = random.choice(MOODS)

def moodify(u, lines):
    mood = u["mood"]

    extras = {
        "happy":["hehe","yay!!"],
        "clingy":["stay… pls","don’t leave"],
        "jealous":["…mine","who was that"],
        "sleepy":["…huh","im sleepy"],
        "chaotic":["WAIT","I DIDNT MEAN THAT"]
    }

    return random.choice(lines) + " " + random.choice(extras[mood])

# ======================
# SYSTEM
# ======================

def update_user(d,gid,u,action=None):
    now=time.time()

    if now-u["last"]>3600:
        u["bond"]=max(0,u["bond"]-1)

    u["bond"]+=1
    u["last"]=now

    if action:
        u["memory"]=u["memory"][-5:]+[action]

    update_mood(u)

# ======================
# SEND
# ======================

async def send(i,msg=None,embed=None,view=None):
    await asyncio.sleep(random.uniform(0.2,0.6))

    if not i.response.is_done():
        await i.response.send_message(content=msg,embed=embed,view=view)
    else:
        await i.followup.send(content=msg,embed=embed,view=view)

# ======================
# GIFS
# ======================

GIFS={
"hug":["https://media.tenor.com/9e1aE7i1kV0AAAAC/anime-hug.gif"],
"pat":["https://media.tenor.com/zrq4G5d0F6kAAAAC/headpat-anime.gif"],
"cuddle":["https://media.tenor.com/0t7G5v6J6eYAAAAC/anime-cuddle.gif"],
"boop":["https://media.tenor.com/5Z1WZz9X6V0AAAAC/anime-boop.gif"]
}

def gif(a): return random.choice(GIFS[a])

# ======================
# SHOP
# ======================

SHOP={
"magnet":(20,"double treat"),
"lucky":(25,"big treat"),
"upgrade":(30,"+1 forever"),
"daily":(30,"double daily"),
"bond":(50,"+10 bond")
}

class ShopView(discord.ui.View):
    def __init__(self,uid):
        super().__init__(timeout=60)
        self.uid=uid

    async def interaction_check(self,i):
        return i.user.id==self.uid

    async def buy(self,i,item):
        d=load_data()
        u=get_user(d,i.guild.id,i.user.id)

        cost=SHOP[item][0]

        if u["treats"]<cost:
            return await i.response.send_message("not enough 💀",ephemeral=True)

        u["treats"]-=cost

        if item=="magnet":u["magnet"]=True
        if item=="lucky":u["lucky"]=True
        if item=="upgrade":u["upgrade"]+=1
        if item=="daily":u["daily"]=True
        if item=="bond":u["bond"]+=10

        save_data(d)

        await i.response.send_message(f"bought {item} 🐾",ephemeral=True)

    @discord.ui.button(label="Magnet",style=discord.ButtonStyle.primary)
    async def m(self,i,b):await self.buy(i,"magnet")

    @discord.ui.button(label="Lucky",style=discord.ButtonStyle.success)
    async def l(self,i,b):await self.buy(i,"lucky")

    @discord.ui.button(label="Boost",style=discord.ButtonStyle.secondary)
    async def u(self,i,b):await self.buy(i,"upgrade")

    @discord.ui.button(label="Daily",style=discord.ButtonStyle.secondary)
    async def d(self,i,b):await self.buy(i,"daily")

    @discord.ui.button(label="Bond",style=discord.ButtonStyle.danger)
    async def b(self,i,b2):await self.buy(i,"bond")

@tree.command(name="shop",description="shop 🐾")
async def shop(i):
    e=discord.Embed(title="🐾 shop",color=0xffb6c1)
    for k,(c,d) in SHOP.items():
        e.add_field(name=f"{k} — {c}",value=d,inline=False)
    await send(i,embed=e,view=ShopView(i.user.id))

# ======================
# INVENTORY
# ======================

@tree.command(name="inventory",description="inventory 🐾")
async def inv(i):
    d=load_data()
    u=get_user(d,i.guild.id,i.user.id)

    e=discord.Embed(title="🎒 inventory",color=0x89CFF0)
    e.add_field(name="treats",value=u["treats"])
    e.add_field(name="bond",value=u["bond"])
    e.add_field(name="mood",value=u["mood"])

    await send(i,embed=e)

# ======================
# ECONOMY
# ======================

@tree.command(name="treat",description="treat 🐾")
async def treat(i):
    d=load_data();u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"treat")

    g=random.randint(5,10)

    if u["magnet"]:g*=2;u["magnet"]=False
    if u["lucky"]:g=random.randint(15,25);u["lucky"]=False

    g+=u["upgrade"]
    u["treats"]+=g

    save_data(d)
    await send(i,f"+{g} treats")

@tree.command(name="daily",description="daily")
async def daily(i):
    d=load_data();u=get_user(d,i.guild.id,i.user.id)

    r=50
    if u["daily"]:r*=2;u["daily"]=False

    u["treats"]+=r
    save_data(d)

    await send(i,f"+{r} daily")

@tree.command(name="coinflip",description="coin")
async def coin(i):
    await send(i,random.choice(["heads","tails"]))

# ======================
# RP
# ======================

@tree.command(name="hug",description="hug")
async def hug(i,m:discord.Member):
    d=load_data();u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"hug");save_data(d)

    lines=[f"*hugs {m.mention}* don’t move"]
    await send(i,moodify(u,lines)+"\n"+gif("hug"))

# ======================
# TROLL / CHAOTIC
# ======================

@tree.command(name="lewd",description="do you mean food..?")
async def lewd(i):
    d=load_data();u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"lewd");save_data(d)

    lines=[
        "lewd… is that edible??",
        "WAIT that sounds illegal",
        "why are you like this 😭",
        "I don’t understand but ok"
    ]

    await send(i,moodify(u,lines))

@tree.command(name="heat",description="oh no…")
async def heat(i):
    d=load_data();u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"heat");save_data(d)

    lines=[
        "WHY AM I WARM",
        "THIS IS YOUR FAULT",
        "something is wrong 😭"
    ]

    await send(i,moodify(u,lines))

@tree.command(name="nsfw",description="DO NOT THE PUPPYGIRL")
async def nsfw(i):
    d=load_data();u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"nsfw");save_data(d)

    lines=[
        "DO NOT ME",
        "I feel unsafe",
        "why would you say that"
    ]

    await send(i,moodify(u,lines))

@tree.command(name="collar",description="…why do you have that")
async def collar(i):
    d=load_data();u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"collar");save_data(d)

    lines=[
        "is that for me??",
        "WAIT I kinda like it",
        "this feels like a trap"
    ]

    await send(i,moodify(u,lines))

@tree.command(name="leash",description="WAIT WAIT WAIT")
async def leash(i):
    d=load_data();u=get_user(d,i.guild.id,i.user.id)
    update_user(d,i.guild.id,u,"leash");save_data(d)

    lines=[
        "WHERE ARE WE GOING",
        "WAIT SLOW DOWN",
        "HEY 😭"
    ]

    await send(i,moodify(u,lines))

# ======================
# PASSIVE
# ======================

@bot.event
async def on_message(msg):
    if msg.author.bot: return

    if "good girl" in msg.content.lower():
        await msg.reply("*tail wagging* WAIT ME??")

    if random.random()<0.03:
        await msg.reply("…hi")

    await bot.process_commands(msg)

# ======================
# READY
# ======================

@bot.event
async def on_ready():
    print("V20 READY")
    await tree.sync()

bot.run(TOKEN)
