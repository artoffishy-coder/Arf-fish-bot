import discord
from discord.ext import commands
from discord import app_commands
import json, os, random, time

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ✅ NEW DATA FILE (no conflicts)
DATA_FILE = "arf_fish_v2.json"

# ---------- SAFE SEND ----------
async def safe_send(i, **kwargs):
    try:
        if not i.response.is_done():
            await i.response.send_message(**kwargs)
        else:
            await i.followup.send(**kwargs)
    except:
        pass

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

def migrate_user(user):
    user.setdefault("xp", 0)
    user.setdefault("level", 0)
    user.setdefault("treats", 100)
    user.setdefault("inventory", [])
    user.setdefault("achievements", [])
    user.setdefault("last_treat", 0)
    user.setdefault("last_beg", 0)
    user.setdefault("last_work", 0)
    user.setdefault("mood", "neutral")
    return user

def get_user(data, gid, uid):
    gid = str(gid) if gid else "global"
    uid = str(uid)

    data.setdefault(gid, {})
    user = data[gid].setdefault(uid, {})

    return migrate_user(user)

# ---------- SYSTEM ----------
MOODS = ["happy","neutral","grumpy","playful"]

def update_mood(u):
    if random.random() < 0.2:
        u["mood"] = random.choice(MOODS)

def mood_bonus(u):
    return 2 if u["mood"]=="happy" else -1 if u["mood"]=="grumpy" else 0

def mood_text(u,t):
    if u["mood"]=="happy": return t+" 😊"
    if u["mood"]=="grumpy": return "hmph… "+t
    if u["mood"]=="playful": return t+" WAN!! 🐶"
    return t

def get_level(xp):
    lvl=0
    while xp >= 100*(lvl+1):
        xp -= 100*(lvl+1)
        lvl += 1
    return lvl

# ---------- ACHIEVEMENTS ----------
ACHIEVEMENTS = {
    "rich":"💰 1000 treats!",
    "level5":"📈 Level 5!"
}

def check_achievements(u):
    new=[]
    if u["treats"]>=1000 and "rich" not in u["achievements"]:
        u["achievements"].append("rich"); new.append("rich")
    if u["level"]>=5 and "level5" not in u["achievements"]:
        u["achievements"].append("level5"); new.append("level5")
    return new

# ---------- SHOP (FULL RESTORED) ----------
SHOP = {
    "xp_boost":{"name":"XP Boost ⚡","price":50,"desc":"Gain more XP"},
    "lucky":{"name":"Lucky Paw 🍀","price":40,"desc":"Better luck"},
    "treat_pack":{"name":"Treat Pack 🦴","price":30,"desc":"Extra treats"},
    "mega_treat":{"name":"Mega Treat 🍖","price":80,"desc":"Big gains"},
    "puppy_snack":{"name":"Puppy Snack 🐶","price":25,"desc":"Cheap snack"},
    "zoomies":{"name":"Zoomies ⚡🐾","price":60,"desc":"Energy boost"},
    "collar":{"name":"Cute Collar 🎀","price":60,"desc":"Style"},
    "golden_bone":{"name":"Golden Bone 🦴✨","price":150,"desc":"Rare flex"},
    "mystery_box":{"name":"Mystery Box 🎁","price":100,"desc":"Random reward"},
    "strange_potion":{"name":"Strange Potion 🧪","price":90,"desc":"Weird effects"}
}

# ---------- ACTIONS ----------
async def treat_action(i):
    d=load_data(); u=get_user(d,i.guild.id if i.guild else None,i.user.id)

    if time.time()-u["last_treat"]<10:
        return "⏱️ Wait!"

    u["last_treat"]=time.time()
    update_mood(u)

    gain=max(random.randint(5,10)+mood_bonus(u),1)
    u["treats"]+=gain
    u["xp"]+=gain
    u["level"]=get_level(u["xp"])

    new=check_achievements(u)
    save_data(d)

    msg=mood_text(u,f"You got **{gain} treats** 🦴")
    for a in new:
        msg+=f"\n🏆 {ACHIEVEMENTS[a]}"
    return msg

async def beg_action(i):
    d=load_data(); u=get_user(d,i.guild.id if i.guild else None,i.user.id)
    if time.time()-u["last_beg"]<60:
        return "⏱️ Too soon!"
    u["last_beg"]=time.time()
    gain=random.randint(10,25)
    u["treats"]+=gain
    save_data(d)
    return mood_text(u,f"You got {gain} treats 🐶")

async def work_action(i):
    d=load_data(); u=get_user(d,i.guild.id if i.guild else None,i.user.id)
    if time.time()-u["last_work"]<120:
        return "⏱️ Too tired!"
    u["last_work"]=time.time()
    gain=random.randint(20,40)
    u["treats"]+=gain
    save_data(d)
    return mood_text(u,f"You earned {gain} treats 💼")

# ---------- UI ----------
class ActionView(discord.ui.View):
    def __init__(self, user_id, user):
        super().__init__(timeout=60)
        self.user_id = user_id

    async def interaction_check(self, interaction):
        return interaction.user.id == self.user_id

    @discord.ui.button(label="Treat 🦴", style=discord.ButtonStyle.primary)
    async def treat_btn(self, i, b):
        msg = await treat_action(i)
        await i.response.edit_message(content=msg, view=self)

    @discord.ui.button(label="Beg 🐶", style=discord.ButtonStyle.secondary)
    async def beg_btn(self, i, b):
        msg = await beg_action(i)
        await i.response.edit_message(content=msg, view=self)

    @discord.ui.button(label="Work 💼", style=discord.ButtonStyle.success)
    async def work_btn(self, i, b):
        msg = await work_action(i)
        await i.response.edit_message(content=msg, view=self)

# ---------- COMMANDS ----------
@tree.command(name="treat", description="Open action panel 🐾")
async def treat(i:discord.Interaction):
    d=load_data(); u=get_user(d,i.guild.id if i.guild else None,i.user.id)
    msg = await treat_action(i)
    await safe_send(i, content=msg, view=ActionView(i.user.id,u))

@tree.command(name="shop", description="View shop 🛒")
async def shop(i:discord.Interaction):
    embed=discord.Embed(title="🛒 Arf-Fish Shop",color=0xFFA500)
    for item in SHOP.values():
        embed.add_field(name=f"{item['name']} — {item['price']} 🦴",value=item["desc"],inline=False)
    await safe_send(i,embed=embed)

@tree.command(name="buy", description="Buy item 🛍️")
async def buy(i:discord.Interaction,item:str):
    item=item.lower().replace(" ","_")
    d=load_data(); u=get_user(d,i.guild.id if i.guild else None,i.user.id)
    if item not in SHOP: return await safe_send(i,"Invalid item")
    if u["treats"]<SHOP[item]["price"]: return await safe_send(i,"Not enough treats")
    u["treats"]-=SHOP[item]["price"]
    u["inventory"].append(SHOP[item]["name"])
    save_data(d)
    await safe_send(i,f"Bought {SHOP[item]['name']}")

@tree.command(name="inventory", description="Check inventory 🎒")
async def inventory(i:discord.Interaction):
    d=load_data(); u=get_user(d,i.guild.id if i.guild else None,i.user.id)
    await safe_send(i,"\n".join(u["inventory"]) or "Empty")

@tree.command(name="leaderboard", description="Top players 🏆")
async def leaderboard(i:discord.Interaction):
    d=load_data(); gid=str(i.guild.id)
    users=d.get(gid,{})
    sorted_users=sorted(users.items(),key=lambda x:x[1]["treats"],reverse=True)
    text="\n".join([f"{idx+1}. <@{uid}> — {u['treats']} 🦴" for idx,(uid,u) in enumerate(sorted_users[:10])])
    await safe_send(i,text or "No data")

# ---------- START ----------
@bot.event
async def on_ready():
    print("🌍 ARF-FISH FINAL BUILD LOADED")
    synced = await tree.sync()
    print(f"🌍 Synced {len(synced)} commands globally")

bot.run(TOKEN)
