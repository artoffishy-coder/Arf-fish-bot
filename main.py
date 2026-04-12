import discord
from discord.ext import commands
from discord import app_commands
import json, os, random, time

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_FILE = "arf_fish_v7.json"

# ---------- SAFE SEND ----------
async def safe_send(i, **kwargs):
    if not i.response.is_done():
        await i.response.send_message(**kwargs)
    else:
        await i.followup.send(**kwargs)

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
    g = str(g)
    u = str(u)
    d.setdefault(g, {})
    d[g].setdefault(u, {
        "xp":0,"level":0,"treats":100,
        "inventory":[],"achievements":[],
        "last_treat":0,"last_beg":0,"last_work":0,"last_daily":0,
        "streak":0,"mood":"neutral"
    })
    return d[g][u]

# ---------- SYSTEM ----------
MOODS = ["happy","neutral","grumpy","playful"]

def update_mood(u):
    if random.random() < 0.2:
        u["mood"] = random.choice(MOODS)

def mood_bonus(u):
    return 2 if u["mood"]=="happy" else -2 if u["mood"]=="grumpy" else 0

def mood_text(u,t):
    if u["mood"]=="playful": return t+" WAN!! 🐶"
    if u["mood"]=="grumpy": return "hmph… "+t
    if u["mood"]=="happy": return t+" *wag*"
    return t

def get_level(xp):
    lvl=0
    while xp>=100*(lvl+1):
        xp-=100*(lvl+1)
        lvl+=1
    return lvl

# ---------- SHOP ----------
SHOP = {
 "xp_boost":{"name":"XP Boost ⚡","price":50},
 "lucky":{"name":"Lucky Paw 🍀","price":40},
 "zoomies":{"name":"Zoomies ⚡🐾","price":60},
 "mystery_box":{"name":"Mystery Box 🎁","price":100},
 "potion":{"name":"Potion 🧪","price":90}
}

# ---------- GIFS ----------
HUG_GIFS = [
"https://media.tenor.com/6f7rF0l1R4cAAAAC/anime-hug.gif",
"https://media.tenor.com/2roX3uxz_68AAAAC/anime-hug.gif",
"https://media.tenor.com/OXCV_qL-V60AAAAC/mochi-peachcat-hug.gif"
]

PAT_GIFS = [
"https://media.tenor.com/Xg6N5Q9Y6gAAAAAC/anime-headpat.gif",
"https://media.tenor.com/Ws6Dm1ZW_vMAAAAC/pat-head.gif"
]

CUDDLE_GIFS = [
"https://media.tenor.com/H2X7b7ZQZbQAAAAC/anime-cuddle.gif",
"https://media.tenor.com/9e1aE7wF9KcAAAAC/anime-cuddle-love.gif"
]

# ---------- TROLL RESPONSES ----------
LEWD_RESPONSES = [
"leans in… slips on banana 🍌",
"tries to be seductive… fails",
"boops instead 👉🐶",
"you expected something else? arf 😏"
]

HEAT_RESPONSES = [
"overheating… zoomies 🐾",
"brain now fluff",
"too many vibes",
"arf… system meltdown"
]

NSFW_TROLL_RESPONSES = [
"🚨 BONK",
"nice try 😭",
"denied",
"go outside"
]

COLLAR_RESPONSES = [
"puts collar… forgets why 🐾",
"stay close!! or not!! idk",
"tail wag… this seems right"
]

LEASH_RESPONSES = [
"tangles leash 😭",
"you lead actually",
"we lost already"
]

# ---------- ACTIONS ----------
async def treat_action(i):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    if time.time()-u["last_treat"]<10:
        return "⏱️ wait…"
    u["last_treat"]=time.time()
    update_mood(u)
    gain=random.randint(5,10)+mood_bonus(u)
    u["treats"]+=gain
    u["xp"]+=gain
    u["level"]=get_level(u["xp"])
    save_data(d)
    return mood_text(u,f"+{gain} treats 🦴")

async def beg_action(i):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    if time.time()-u["last_beg"]<60:
        return "too soon…"
    u["last_beg"]=time.time()
    gain=random.randint(10,25)
    u["treats"]+=gain
    save_data(d)
    return f"*puppy eyes* +{gain} 🐶"

async def work_action(i):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    if time.time()-u["last_work"]<120:
        return "too tired…"
    u["last_work"]=time.time()
    gain=random.randint(20,40)
    u["treats"]+=gain
    save_data(d)
    return f"*worked* +{gain} 💼"

# ---------- UI ----------
class ActionView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid

    async def interaction_check(self, i):
        return i.user.id == self.uid

    @discord.ui.button(label="Treat 🦴", style=discord.ButtonStyle.primary)
    async def t(self, i, b):
        await i.response.edit_message(content=await treat_action(i), view=self)

    @discord.ui.button(label="Beg 🐶", style=discord.ButtonStyle.secondary)
    async def b(self, i, b2):
        await i.response.edit_message(content=await beg_action(i), view=self)

    @discord.ui.button(label="Work 💼", style=discord.ButtonStyle.success)
    async def w(self, i, b3):
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
    if time.time()-u["last_daily"]<86400:
        return await safe_send(i, content="come back later")
    u["last_daily"]=time.time()
    u["streak"]+=1
    reward=50+(u["streak"]*5)
    u["treats"]+=reward
    save_data(d)
    await safe_send(i, content=f"+{reward} (streak {u['streak']})")

@tree.command(name="shop", description="Shop 🛒")
async def shop(i: discord.Interaction):
    txt="\n".join([f"{v['name']} — {v['price']}" for v in SHOP.values()])
    await safe_send(i, content=txt)

@tree.command(name="buy", description="Buy item")
async def buy(i: discord.Interaction, item: str):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    item=item.lower().replace(" ","_")
    if item not in SHOP:
        return await safe_send(i, content="invalid")
    if u["treats"]<SHOP[item]["price"]:
        return await safe_send(i, content="not enough")
    u["treats"]-=SHOP[item]["price"]
    u["inventory"].append(SHOP[item]["name"])
    save_data(d)
    await safe_send(i, content="bought")

@tree.command(name="inventory", description="Inventory 🎒")
async def inventory(i: discord.Interaction):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    await safe_send(i, content="\n".join(u["inventory"]) or "empty")

@tree.command(name="leaderboard", description="Leaderboard 🏆")
async def leaderboard(i: discord.Interaction):
    d=load_data(); g=str(i.guild.id)
    users=d.get(g,{})
    top=sorted(users.items(),key=lambda x:x[1]["treats"],reverse=True)
    txt="\n".join([f"{i+1}. <@{uid}> {u['treats']}" for i,(uid,u) in enumerate(top[:10])])
    await safe_send(i, content=txt or "none")

# ---------- RP ----------
@tree.command(name="hug", description="Hug 🤗")
async def hug(i: discord.Interaction, member: discord.Member=None):
    embed=discord.Embed(description=f"{i.user.mention} hugs {member or i.user}")
    embed.set_image(url=random.choice(HUG_GIFS))
    await safe_send(i, embed=embed)

@tree.command(name="pat", description="Pat 🐶")
async def pat(i: discord.Interaction, member: discord.Member=None):
    embed=discord.Embed(description=f"{i.user.mention} pats {member or i.user}")
    embed.set_image(url=random.choice(PAT_GIFS))
    await safe_send(i, embed=embed)

@tree.command(name="cuddle", description="Cuddle 💖")
async def cuddle(i: discord.Interaction, member: discord.Member=None):
    embed=discord.Embed(description=f"{i.user.mention} cuddles {member or i.user}")
    embed.set_image(url=random.choice(CUDDLE_GIFS))
    await safe_send(i, embed=embed)

# ---------- TROLL ----------
@tree.command(name="lewd", description="??? 😏")
async def lewd(i: discord.Interaction):
    await safe_send(i, content=random.choice(LEWD_RESPONSES))

@tree.command(name="heat", description="Something off 🐾")
async def heat(i: discord.Interaction):
    await safe_send(i, content=random.choice(HEAT_RESPONSES))

@tree.command(name="nsfw", description="Try it")
async def nsfw(i: discord.Interaction):
    await safe_send(i, content=random.choice(NSFW_TROLL_RESPONSES))

@tree.command(name="collar", description="Collar 🐾")
async def collar(i: discord.Interaction, member: discord.Member):
    await safe_send(i, content=f"{i.user.mention} -> {member.mention}\n{random.choice(COLLAR_RESPONSES)}")

@tree.command(name="leash", description="Leash 🐕")
async def leash(i: discord.Interaction, member: discord.Member):
    await safe_send(i, content=f"{i.user.mention} -> {member.mention}\n{random.choice(LEASH_RESPONSES)}")

# ---------- START ----------
@bot.event
async def on_ready():
    print("🔥 V7 FINAL READY")
    synced = await tree.sync()
    print(f"Synced {len(synced)} commands")

bot.run(TOKEN)
