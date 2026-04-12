import discord
from discord.ext import commands
from discord import app_commands
import json, os, random, time

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_FILE = "data.json"

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
    except Exception:
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

# ---------------- ACHIEVEMENTS ----------------
ACHIEVEMENTS = {
    "rich": "💰 Reached 1000 treats!",
    "level5": "📈 Reached level 5!"
}

def check_achievements(user):
    new=[]
    if user["treats"]>=1000 and "rich" not in user["achievements"]:
        user["achievements"].append("rich"); new.append("rich")
    if user["level"]>=5 and "level5" not in user["achievements"]:
        user["achievements"].append("level5"); new.append("level5")
    return new

# ---------------- SHOP ----------------
SHOP = {
    "xp_boost": {"name":"XP Boost ⚡","price":50,"desc":"Gain extra XP"},
    "lucky": {"name":"Lucky Paw 🍀","price":40,"desc":"Better rewards"}
}

# ---------------- UI ----------------
class TreatView(discord.ui.View):
    def __init__(self, uid, user):
        super().__init__(timeout=60)
        self.uid = uid
        now=time.time()
        self.treat_btn.disabled = now-user["last_treat"]<10
        self.beg_btn.disabled = now-user["last_beg"]<60
        self.work_btn.disabled = now-user["last_work"]<120

    async def interaction_check(self,i): return i.user.id==self.uid

    @discord.ui.button(label="Treat 🦴",style=discord.ButtonStyle.primary)
    async def treat_btn(self,i,b):
        await i.response.defer()
        await handle_treat(i)

    @discord.ui.button(label="Beg 🐶",style=discord.ButtonStyle.secondary)
    async def beg_btn(self,i,b):
        await i.response.defer()
        await handle_beg(i)

    @discord.ui.button(label="Work 💼",style=discord.ButtonStyle.success)
    async def work_btn(self,i,b):
        await i.response.defer()
        await handle_work(i)

# ---------------- ACTIONS ----------------
async def handle_treat(i):
    data=load_data(); gid,uid=get_ids(i); u=get_user(data,gid,uid)

    if time.time()-u["last_treat"]<10:
        return await safe_send(i,"⏱️ Wait!",ephemeral=True)

    u["last_treat"]=time.time(); update_mood(u)
    gain=max(random.randint(5,10)+mood_bonus(u),1)

    u["treats"]+=gain; u["xp"]+=gain; u["level"]=get_level(u["xp"])
    new=check_achievements(u); save_data(data)

    msg=mood_text(u,f"You got **{gain} treats** 🦴")
    for a in new: msg+=f"\n🏆 {ACHIEVEMENTS[a]}"

    await safe_send(i,msg,view=TreatView(uid,u))

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
    await safe_send(i,embed=discord.Embed(title="Shop",description=desc))

@tree.command(name="buy", description="Buy item 🛍️")
async def buy(i:discord.Interaction,item:str):
    data=load_data(); u=get_user(data,i.guild.id if i.guild else None,i.user.id)

    if item not in SHOP: return await safe_send(i,"Invalid item")
    if u["treats"]<SHOP[item]["price"]: return await safe_send(i,"Not enough treats")

    u["treats"]-=SHOP[item]["price"]
    u["inventory"].append(SHOP[item]["name"])
    save_data(data)

    await safe_send(i,f"Bought {SHOP[item]['name']}")

@tree.command(name="inventory", description="Check inventory 🎒")
async def inventory(i:discord.Interaction):
    data=load_data(); u=get_user(data,i.guild.id if i.guild else None,i.user.id)
    items="\n".join(u["inventory"]) or "Empty"
    await safe_send(i,embed=discord.Embed(title="Inventory",description=items))

@tree.command(name="achievements", description="View achievements 🏆")
async def achievements(i:discord.Interaction):
    data=load_data(); u=get_user(data,i.guild.id if i.guild else None,i.user.id)
    text="\n".join([ACHIEVEMENTS[a] for a in u["achievements"]]) or "None"
    await safe_send(i,embed=discord.Embed(title="Achievements",description=text))

@tree.command(name="leaderboard", description="Top players 🏆")
async def leaderboard(i:discord.Interaction):
    data=load_data(); gid=str(i.guild.id)
    users=data.get(gid,{})
    sorted_users=sorted(users.items(),key=lambda x:x[1]["treats"],reverse=True)

    desc=""
    for idx,(uid,u) in enumerate(sorted_users[:10],1):
        desc+=f"{idx}. <@{uid}> — {u['treats']} 🦴\n"

    await safe_send(i,embed=discord.Embed(title="Leaderboard",description=desc))

# ---------------- RP ----------------
@tree.command(name="hug", description="Hug someone 🤗")
async def hug(i:discord.Interaction,m:discord.Member=None):
    t=m.mention if m else i.user.mention
    await safe_send(i,f"{i.user.mention} hugs {t} 🤗")

@tree.command(name="pat", description="Pat someone 🐶")
async def pat(i:discord.Interaction,m:discord.Member=None):
    t=m.mention if m else i.user.mention
    await safe_send(i,f"{i.user.mention} pats {t}")

@tree.command(name="cuddle", description="Cuddle someone 💖")
async def cuddle(i:discord.Interaction,m:discord.Member=None):
    t=m.mention if m else i.user.mention
    await safe_send(i,f"{i.user.mention} cuddles {t}")

# ---------------- TROLL ----------------
@tree.command(name="heat", description="Feeling needy 😳")
async def heat(i:discord.Interaction):
    await safe_send(i,"WAN… you’re acting up 🐶")

@tree.command(name="lewd", description="Test your luck 😈")
async def lewd(i:discord.Interaction):
    await safe_send(i,"I saw that. behave.")

@tree.command(name="breed", description="No.")
async def breed(i:discord.Interaction,m:discord.Member=None):
    t=m.mention if m else i.user.mention
    await safe_send(i,f"{t} — nope.")

# ---------------- HELP ----------------
@tree.command(name="help", description="View commands 🐾")
async def help_cmd(i:discord.Interaction):
    await safe_send(i,"Use / to explore commands!")

# ---------------- START ----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    synced=await tree.sync()
    print(f"✅ Synced {len(synced)} commands")

bot.run(TOKEN)
