import discord
from discord.ext import commands
from discord import app_commands
import json, os, random, time

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# 🔥 FORCE NEW DATABASE
DATA_FILE = "fresh_data_v2.json"

# ---------------- SAFE SEND ----------------
async def safe_send(interaction, content=None, embed=None, view=None, ephemeral=False):
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                content=content, embed=embed, view=view, ephemeral=ephemeral
            )
        else:
            await interaction.followup.send(
                content=content, embed=embed, view=view, ephemeral=ephemeral
            )
    except:
        try:
            await interaction.followup.send(
                content=content, embed=embed, view=view, ephemeral=ephemeral
            )
        except:
            pass

# ---------------- DATA ----------------
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

def get_ids(i):
    gid = i.guild.id if i.guild else None
    return gid, i.user.id

# ---------------- LEVEL ----------------
def xp_for_level(level): return 100 * level

def get_level(xp):
    lvl = 0
    while xp >= xp_for_level(lvl+1):
        xp -= xp_for_level(lvl+1)
        lvl += 1
    return lvl

# ---------------- MOOD ----------------
MOODS = ["happy","neutral","grumpy","playful"]

def update_mood(user):
    if random.random() < 0.2:
        user["mood"] = random.choice(MOODS)

def mood_bonus(user):
    return 2 if user["mood"]=="happy" else -1 if user["mood"]=="grumpy" else 0

def mood_text(user,text):
    if user["mood"]=="happy": return text+" 😊"
    if user["mood"]=="grumpy": return "hmph… "+text
    if user["mood"]=="playful": return text+" WAN!! 🐶"
    return text

# ---------------- SHOP ----------------
SHOP = {
    "xp_boost": {"name":"XP Boost ⚡","price":50,"desc":"Gain extra XP"},
    "lucky": {"name":"Lucky Paw 🍀","price":40,"desc":"Better rewards"}
}

# ---------------- ACTIONS ----------------
async def handle_treat(i):
    data=load_data(); gid,uid=get_ids(i); u=get_user(data,gid,uid)

    if time.time()-u["last_treat"]<10:
        return await safe_send(i,"⏱️ Wait!",ephemeral=True)

    u["last_treat"]=time.time(); update_mood(u)
    gain=max(random.randint(5,10)+mood_bonus(u),1)

    u["treats"]+=gain; u["xp"]+=gain; u["level"]=get_level(u["xp"])
    save_data(data)

    await safe_send(i,mood_text(u,f"You got **{gain} treats** 🦴"))

async def handle_beg(i):
    data=load_data(); gid,uid=get_ids(i); u=get_user(data,gid,uid)

    if time.time()-u["last_beg"]<60:
        return await safe_send(i,"⏱️ Too soon!",ephemeral=True)

    u["last_beg"]=time.time()
    gain=random.randint(10,25)
    u["treats"]+=gain; save_data(data)

    await safe_send(i,mood_text(u,f"You got **{gain} treats** 🐶"))

async def handle_work(i):
    data=load_data(); gid,uid=get_ids(i); u=get_user(data,gid,uid)

    if time.time()-u["last_work"]<120:
        return await safe_send(i,"⏱️ Too tired!",ephemeral=True)

    u["last_work"]=time.time()
    gain=random.randint(20,40)
    u["treats"]+=gain; save_data(data)

    await safe_send(i,mood_text(u,f"You earned **{gain} treats** 💼"))

# ---------------- COMMANDS ----------------
@tree.command(name="treat", description="Get treats and XP 🦴")
async def treat(i:discord.Interaction): await handle_treat(i)

@tree.command(name="beg", description="Beg for extra treats 🐶")
async def beg(i:discord.Interaction): await handle_beg(i)

@tree.command(name="work", description="Work to earn more treats 💼")
async def work(i:discord.Interaction): await handle_work(i)

@tree.command(name="shop", description="View shop 🛒")
async def shop(i:discord.Interaction):
    desc="\n".join([f"{v['name']} — {v['price']} 🦴" for v in SHOP.values()])
    await safe_send(i,embed=discord.Embed(title="🛒 Shop",description=desc))

@tree.command(name="inventory", description="Check inventory 🎒")
async def inventory(i:discord.Interaction):
    data=load_data(); u=get_user(data,i.guild.id if i.guild else None,i.user.id)
    items="\n".join(u["inventory"]) or "Empty"
    await safe_send(i,embed=discord.Embed(title="🎒 Inventory",description=items))

# ---------------- DEBUG START ----------------
@bot.event
async def on_ready():
    print("🔥 NEW VERSION LOADED 🔥")
    print(f"Logged in as {bot.user}")

    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Sync error: {e}")

bot.run(TOKEN)
