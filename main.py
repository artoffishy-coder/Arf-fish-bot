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
        return json.load(open(DATA_FILE))
    return {}

def save_data(data):
    json.dump(data, open(DATA_FILE, "w"), indent=2)

def get_user(data, gid, uid):
    gid = str(gid) if gid else "global"
    uid = str(uid)

    data.setdefault(gid, {})
    user = data[gid].setdefault(uid, {})

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

# ---------- SYSTEMS ----------
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

# ---------- SHOP ----------
SHOP = {
    "xp_boost":{"name":"XP Boost ⚡","price":50},
    "lucky":{"name":"Lucky Paw 🍀","price":40}
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

# ---------- UI PANEL ----------
class ActionView(discord.ui.View):
    def __init__(self, user_id, user):
        super().__init__(timeout=60)
        self.user_id = user_id

        now = time.time()
        self.treat_btn.disabled = now - user["last_treat"] < 10
        self.beg_btn.disabled = now - user["last_beg"] < 60
        self.work_btn.disabled = now - user["last_work"] < 120

    async def interaction_check(self, interaction):
        return interaction.user.id == self.user_id

    @discord.ui.button(label="Treat 🦴", style=discord.ButtonStyle.primary)
    async def treat_btn(self, interaction, button):
        msg = await treat_action(interaction)
        d=load_data(); u=get_user(d,interaction.guild.id if interaction.guild else None,interaction.user.id)
        await interaction.response.edit_message(content=msg, view=ActionView(self.user_id,u))

    @discord.ui.button(label="Beg 🐶", style=discord.ButtonStyle.secondary)
    async def beg_btn(self, interaction, button):
        msg = await beg_action(interaction)
        d=load_data(); u=get_user(d,interaction.guild.id if interaction.guild else None,interaction.user.id)
        await interaction.response.edit_message(content=msg, view=ActionView(self.user_id,u))

    @discord.ui.button(label="Work 💼", style=discord.ButtonStyle.success)
    async def work_btn(self, interaction, button):
        msg = await work_action(interaction)
        d=load_data(); u=get_user(d,interaction.guild.id if interaction.guild else None,interaction.user.id)
        await interaction.response.edit_message(content=msg, view=ActionView(self.user_id,u))

# ---------- COMMANDS ----------
@tree.command(name="treat", description="Open action panel 🐾")
async def treat(i:discord.Interaction):
    d=load_data(); u=get_user(d,i.guild.id if i.guild else None,i.user.id)
    msg = await treat_action(i)
    await safe_send(i, content=msg, view=ActionView(i.user.id,u))

# (rest of commands stay same as before — shop, buy, leaderboard, rp, etc.)

# ---------- START ----------
@bot.event
async def on_ready():
    print("ARF-FISH UI BUILD LOADED")
    synced=await tree.sync()
    print(f"✅ Synced {len(synced)} commands")

bot.run(TOKEN)
