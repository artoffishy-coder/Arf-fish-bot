# FINAL ARF-FISH BUILD (NO DEBUG)

import discord
from discord.ext import commands
from discord import app_commands
import json, os, random, time

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_FILE = "arf_fish_data.json"

# ---------- SAFE SEND ----------
async def safe_send(i, content=None, embed=None, view=None, ephemeral=False):
    if not i.response.is_done():
        await i.response.send_message(content=content, embed=embed, view=view, ephemeral=ephemeral)
    else:
        await i.followup.send(content=content, embed=embed, view=view, ephemeral=ephemeral)

# ---------- DATA ----------
def load_data():
    if os.path.exists(DATA_FILE):
        return json.load(open(DATA_FILE))
    return {}

def save_data(data):
    json.dump(data, open(DATA_FILE, "w"), indent=2)

def get_user(data, gid, uid):
    gid = str(gid) if gid else "global"
    uid = str(uid)

    data.setdefault(gid, {})
    data[gid].setdefault(uid, {
        "xp":0,"level":0,"treats":100,
        "inventory":[],"achievements":[],
        "last_treat":0,"last_beg":0,"last_work":0,
        "mood":"neutral"
    })
    return data[gid][uid]

# ---------- SYSTEMS ----------
MOODS=["happy","neutral","grumpy","playful"]

def update_mood(u):
    if random.random()<0.2:
        u["mood"]=random.choice(MOODS)

def mood_bonus(u):
    return 2 if u["mood"]=="happy" else -1 if u["mood"]=="grumpy" else 0

def mood_text(u,t):
    if u["mood"]=="happy": return t+" 😊"
    if u["mood"]=="grumpy": return "hmph… "+t
    if u["mood"]=="playful": return t+" WAN!! 🐶"
    return t

def get_level(xp):
    lvl=0
    while xp>=100*(lvl+1):
        xp-=100*(lvl+1)
        lvl+=1
    return lvl

# ---------- SHOP ----------
SHOP={
 "xp_boost":{"name":"XP Boost ⚡","price":50},
 "lucky":{"name":"Lucky Paw 🍀","price":40}
}

# ---------- ACTIONS ----------
async def treat_action(i):
    d=load_data(); u=get_user(d,i.guild.id if i.guild else None,i.user.id)

    if time.time()-u["last_treat"]<10:
        return await safe_send(i,"⏱️ Slow down!",ephemeral=True)

    u["last_treat"]=time.time()
    update_mood(u)

    gain=max(random.randint(5,10)+mood_bonus(u),1)
    u["treats"]+=gain
    u["xp"]+=gain
    u["level"]=get_level(u["xp"])

    save_data(d)

    await safe_send(i,mood_text(u,f"You got **{gain} treats** 🦴"))

# ---------- COMMANDS ----------
@tree.command(name="treat", description="Get treats 🦴")
async def treat(i:discord.Interaction): await treat_action(i)

@tree.command(name="beg", description="Beg for treats 🐶")
async def beg(i:discord.Interaction):
    d=load_data(); u=get_user(d,i.guild.id if i.guild else None,i.user.id)
    if time.time()-u["last_beg"]<60:
        return await safe_send(i,"⏱️ Too soon!",ephemeral=True)
    u["last_beg"]=time.time()
    gain=random.randint(10,25)
    u["treats"]+=gain
    save_data(d)
    await safe_send(i,f"You got {gain} treats 🐶")

@tree.command(name="work", description="Work for treats 💼")
async def work(i:discord.Interaction):
    d=load_data(); u=get_user(d,i.guild.id if i.guild else None,i.user.id)
    if time.time()-u["last_work"]<120:
        return await safe_send(i,"⏱️ Too tired!",ephemeral=True)
    u["last_work"]=time.time()
    gain=random.randint(20,40)
    u["treats"]+=gain
    save_data(d)
    await safe_send(i,f"You earned {gain} treats 💼")

@tree.command(name="shop", description="View shop 🛒")
async def shop(i:discord.Interaction):
    text="\n".join([f"{v['name']} — {v['price']} 🦴" for v in SHOP.values()])
    await safe_send(i,embed=discord.Embed(title="Shop",description=text))

@tree.command(name="inventory", description="Inventory 🎒")
async def inventory(i:discord.Interaction):
    d=load_data(); u=get_user(d,i.guild.id if i.guild else None,i.user.id)
    await safe_send(i,"\n".join(u["inventory"]) or "Empty")

# ---------- READY ----------
@bot.event
async def on_ready():
    print("FINAL BUILD LOADED")
    synced=await tree.sync()
    print(f"Synced {len(synced)} commands")

bot.run(TOKEN)
