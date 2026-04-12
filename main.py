import discord
from discord.ext import commands
from discord import app_commands
import json, os, random, time

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_FILE = "arf_fish_v4.json"

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

def migrate_user(u):
    u.setdefault("xp",0)
    u.setdefault("level",0)
    u.setdefault("treats",100)
    u.setdefault("inventory",[])
    u.setdefault("achievements",[])
    u.setdefault("last_treat",0)
    u.setdefault("last_beg",0)
    u.setdefault("last_work",0)
    u.setdefault("last_daily",0)
    u.setdefault("streak",0)
    u.setdefault("mood","neutral")
    return u

def get_user(d,g,u):
    g=str(g) if g else "global"
    u=str(u)
    d.setdefault(g,{})
    return migrate_user(d[g].setdefault(u,{}))

# ---------- SYSTEM ----------
MOODS=["happy","neutral","grumpy","playful"]

def update_mood(u):
    if random.random()<0.2:
        u["mood"]=random.choice(MOODS)

def mood_bonus(u):
    return 2 if u["mood"]=="happy" else -2 if u["mood"]=="grumpy" else 0

def mood_text(u,t):
    if u["mood"]=="playful": return t+" WAN!! 🐶"
    if u["mood"]=="grumpy": return "hmph… "+t
    if u["mood"]=="happy": return t+" *happy wag*"
    return t

def get_level(xp):
    lvl=0
    while xp>=100*(lvl+1):
        xp-=100*(lvl+1)
        lvl+=1
    return lvl

# ---------- ACHIEVEMENTS ----------
ACHIEVEMENTS={
    "rich":"💰 1000 treats",
    "level5":"📈 level 5"
}

def check_achievements(u):
    new=[]
    if u["treats"]>=1000 and "rich" not in u["achievements"]:
        u["achievements"].append("rich"); new.append("rich")
    if u["level"]>=5 and "level5" not in u["achievements"]:
        u["achievements"].append("level5"); new.append("level5")
    return new

# ---------- SHOP ----------
SHOP={
 "xp_boost":{"name":"XP Boost ⚡","price":50},
 "lucky":{"name":"Lucky Paw 🍀","price":40},
 "zoomies":{"name":"Zoomies ⚡🐾","price":60},
 "mystery_box":{"name":"Mystery Box 🎁","price":100},
 "strange_potion":{"name":"Potion 🧪","price":90}
}

# ---------- EFFECTS ----------
def apply_item_effects(u,g):
    if "XP Boost ⚡" in u["inventory"]:
        g*=2
    if "Lucky Paw 🍀" in u["inventory"]:
        g+=random.randint(2,5)
    return g

def cooldown_reduce(u,cd):
    if "Zoomies ⚡🐾" in u["inventory"]:
        return cd*0.7
    return cd

# ---------- ACTIONS ----------
async def treat_action(i):
    d=load_data(); u=get_user(d,i.guild.id if i.guild else None,i.user.id)

    if time.time()-u["last_treat"]<cooldown_reduce(u,10):
        return "⏱️ wait… need pats…"

    u["last_treat"]=time.time()
    update_mood(u)

    gain=apply_item_effects(u,random.randint(5,10)+mood_bonus(u))
    gain=max(gain,1)

    u["treats"]+=gain
    u["xp"]+=gain
    u["level"]=get_level(u["xp"])

    new=check_achievements(u)

    save_data(d)

    msg=mood_text(u,f"got {gain} treats 🦴")
    for a in new:
        msg+=f"\n🏆 {ACHIEVEMENTS[a]}"
    return msg

async def beg_action(i):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)

    if time.time()-u["last_beg"]<cooldown_reduce(u,60):
        return "too soon… whine…"

    u["last_beg"]=time.time()
    gain=apply_item_effects(u,random.randint(10,25))

    u["treats"]+=gain
    save_data(d)
    return mood_text(u,f"*puppy eyes* got {gain} treats 🐶")

async def work_action(i):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)

    if time.time()-u["last_work"]<cooldown_reduce(u,120):
        return "too tired… nap…"

    u["last_work"]=time.time()
    gain=apply_item_effects(u,random.randint(20,40))

    u["treats"]+=gain
    save_data(d)
    return mood_text(u,f"*works hard* earned {gain} 💼")

# ---------- UI ----------
class ActionView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid=uid

    async def interaction_check(self,i):
        return i.user.id==self.uid

    @discord.ui.button(label="Treat 🦴",style=discord.ButtonStyle.primary)
    async def t(self,i,b):
        await i.response.edit_message(content=await treat_action(i),view=self)

    @discord.ui.button(label="Beg 🐶",style=discord.ButtonStyle.secondary)
    async def b(self,i,b2):
        await i.response.edit_message(content=await beg_action(i),view=self)

    @discord.ui.button(label="Work 💼",style=discord.ButtonStyle.success)
    async def w(self,i,b3):
        await i.response.edit_message(content=await work_action(i),view=self)

# ---------- RP GIFS ----------
HUG_GIFS=[
 "https://media.tenor.com/8Q2R3kUuS8cAAAAC/anime-hug.gif",
 "https://media.tenor.com/0AVbKGY_MxMAAAAC/anime-hug.gif"
]
PAT_GIFS=[
 "https://media.tenor.com/Xg6N5Q9Y6gAAAAAC/anime-headpat.gif"
]
CUDDLE_GIFS=[
 "https://media.tenor.com/H2X7b7ZQZbQAAAAC/anime-cuddle.gif"
]

# ---------- COMMANDS ----------
@tree.command(name="treat",description="Main panel 🐾")
async def treat(i:discord.Interaction):
    await safe_send(i,await treat_action(i),view=ActionView(i.user.id))

@tree.command(name="beg",description="Beg 🐶")
async def beg(i:discord.Interaction):
    await safe_send(i,await beg_action(i))

@tree.command(name="work",description="Work 💼")
async def work(i:discord.Interaction):
    await safe_send(i,await work_action(i))

@tree.command(name="daily",description="Daily reward 🎁")
async def daily(i:discord.Interaction):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)

    if time.time()-u["last_daily"]<86400:
        return await safe_send(i,"come back later…")

    u["last_daily"]=time.time()
    u["streak"]+=1

    reward=50+(u["streak"]*5)
    u["treats"]+=reward

    save_data(d)
    await safe_send(i,f"daily! {reward} treats (streak {u['streak']})")

@tree.command(name="shop",description="Shop 🛒")
async def shop(i:discord.Interaction):
    txt="\n".join([f"{v['name']} — {v['price']}" for v in SHOP.values()])
    await safe_send(i,txt)

@tree.command(name="buy",description="Buy item")
async def buy(i:discord.Interaction,item:str):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    item=item.lower().replace(" ","_")

    if item not in SHOP:
        return await safe_send(i,"invalid item")

    if u["treats"]<SHOP[item]["price"]:
        return await safe_send(i,"not enough")

    u["treats"]-=SHOP[item]["price"]

    if item=="mystery_box":
        bonus=random.randint(20,100)
        u["treats"]+=bonus
        msg=f"🎁 got {bonus}"

    elif item=="strange_potion":
        u["mood"]=random.choice(MOODS)
        msg=f"🧪 mood: {u['mood']}"

    else:
        u["inventory"].append(SHOP[item]["name"])
        msg=f"bought {SHOP[item]['name']}"

    save_data(d)
    await safe_send(i,msg)

@tree.command(name="inventory",description="Inventory 🎒")
async def inventory(i:discord.Interaction):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    await safe_send(i,"\n".join(u["inventory"]) or "empty")

@tree.command(name="leaderboard",description="Leaderboard 🏆")
async def leaderboard(i:discord.Interaction):
    d=load_data(); g=str(i.guild.id)
    users=d.get(g,{})
    top=sorted(users.items(),key=lambda x:x[1]["treats"],reverse=True)
    txt="\n".join([f"{i+1}. <@{uid}> {u['treats']}" for i,(uid,u) in enumerate(top[:10])])
    await safe_send(i,txt or "no data")

@tree.command(name="achievements",description="Achievements 🏅")
async def achievements(i:discord.Interaction):
    d=load_data(); u=get_user(d,i.guild.id,i.user.id)
    txt="\n".join([ACHIEVEMENTS[a] for a in u["achievements"]]) or "none"
    await safe_send(i,txt)

@tree.command(name="hug",description="Hug 🤗")
async def hug(i:discord.Interaction,member:discord.Member=None):
    e=discord.Embed(description=f"{i.user.mention} hugs {(member or i.user).mention}")
    e.set_image(url=random.choice(HUG_GIFS))
    await safe_send(i,embed=e)

@tree.command(name="pat",description="Pat 🐶")
async def pat(i:discord.Interaction,member:discord.Member=None):
    e=discord.Embed(description=f"{i.user.mention} pats {(member or i.user).mention}")
    e.set_image(url=random.choice(PAT_GIFS))
    await safe_send(i,embed=e)

@tree.command(name="cuddle",description="Cuddle 💖")
async def cuddle(i:discord.Interaction,member:discord.Member=None):
    e=discord.Embed(description=f"{i.user.mention} cuddles {(member or i.user).mention}")
    e.set_image(url=random.choice(CUDDLE_GIFS))
    await safe_send(i,embed=e)

@tree.command(name="help",description="Help 📜")
async def help_cmd(i:discord.Interaction):
    await safe_send(i,"/treat /beg /work /daily /shop /buy /inventory /leaderboard /achievements /hug /pat /cuddle")

# ---------- START ----------
@bot.event
async def on_ready():
    print("🔥 TRUE FINAL BUILD LOADED")
    synced=await tree.sync()
    print(f"Synced {len(synced)} commands")

bot.run(TOKEN)
