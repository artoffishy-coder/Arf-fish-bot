import discord
from discord import app_commands
from discord.ext import commands

import json
import os
import random
import time


# =========================================================
# ARF-FISH v0.1
# =========================================================

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise RuntimeError("TOKEN environment variable is missing.")


# =========================================================
# BOT SETUP
# =========================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

tree = bot.tree


# =========================================================
# FILES
# =========================================================

DATA_FILE = "arf_data.json"


# =========================================================
# DATA SYSTEM
# =========================================================

def load_data():
    """Load all saved Arf data."""

    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        print("WARNING: Could not load data file. Starting with empty data.")
        return {}


def save_data(data):
    """Save all Arf data."""

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def get_user(data, guild_id, user_id):
    """
    Get a user's profile.

    Creates the profile if it doesn't exist yet.
    """

    guild_id = str(guild_id)
    user_id = str(user_id)

    # Create guild section
    if guild_id not in data:
        data[guild_id] = {}

    # Create user section
    if user_id not in data[guild_id]:
        data[guild_id][user_id] = {
            "treats": 0,

            "inventory": {},

            "upgrade_level": 0,

            "location": "Backyard",

            "last_dig": 0
        }

    return data[guild_id][user_id]


# =========================================================
# DIGGING
# =========================================================

DIG_COOLDOWN = 4.0
MIN_DIG_COOLDOWN = 1.5


# =========================================================
# READY EVENT
# =========================================================

@bot.event
async def on_ready():

    print(f"Logged in as {bot.user}")

    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} slash command(s).")

    except Exception as error:
        print(f"Command sync failed: {error}")


# =========================================================
# /START
# =========================================================

@tree.command(
    name="start",
    description="Start your adventure with Arf-fish."
)
async def start(interaction: discord.Interaction):

    data = load_data()

    get_user(
        data,
        interaction.guild.id,
        interaction.user.id
    )

    save_data(data)

    embed = discord.Embed(
        title="🐾 Welcome to Arf-fish!",
        description=(
            "Arf is a chaotic little hoarder who likes finding stuff.\n\n"

            "⛏️ **Dig** — find things buried around your location.\n"
            "🎒 **Bag** — see what you've found.\n"
            "🎁 **Give** — trade your findings for treats.\n"
            "🛒 **Shop** — spend treats on upgrades.\n"
            "🗺️ **Journey** — explore new places.\n\n"

            "That's basically it.\n\n"

            "**Go dig something up.** 🐾"
        )
    )

    embed.set_footer(text="Arf-fish 🐟")

    await interaction.response.send_message(embed=embed)


# =========================================================
# /HELP
# =========================================================

@tree.command(
    name="help",
    description="Learn how Arf-fish works."
)
async def help_command(interaction: discord.Interaction):

    embed = discord.Embed(
        title="📖 Arf-fish Help",
        description="Here's the important stuff!",
    )

    embed.add_field(
        name="⛏️ /dig",
        value="Dig around your current location and find something.",
        inline=False
    )

    embed.add_field(
        name="🎒 /inventory",
        value="Look at the things you've collected.",
        inline=False
    )

    embed.add_field(
        name="🎁 /give",
        value="Give your collected items to Arf for treats.",
        inline=False
    )

    embed.add_field(
        name="🛒 /shop",
        value="Spend treats on upgrades.",
        inline=False
    )

    embed.add_field(
        name="🗺️ /journey",
        value="Travel to new locations.",
        inline=False
    )

    embed.set_footer(text="More commands will appear as Arf grows! 🐾")

    await interaction.response.send_message(embed=embed)


# =========================================================
# /DIG
# =========================================================

@tree.command(
    name="dig",
    description="Dig around and find something."
)
async def dig(interaction: discord.Interaction):

    data = load_data()

    user = get_user(
        data,
        interaction.guild.id,
        interaction.user.id
    )

    now = time.time()

    # -----------------------------------------
    # Calculate cooldown
    # -----------------------------------------

    cooldown = max(
        MIN_DIG_COOLDOWN,
        DIG_COOLDOWN - (user["upgrade_level"] * 0.5)
    )

    elapsed = now - user["last_dig"]

    # -----------------------------------------
    # Still on cooldown
    # -----------------------------------------

    if elapsed < cooldown:

        remaining = cooldown - elapsed

        await interaction.response.send_message(
            f"⏳ Arf needs a moment!\n"
            f"Try digging again in **{remaining:.1f}s**.",
            ephemeral=True
        )

        return

    # -----------------------------------------
    # Loot table
    # -----------------------------------------

    loot_table = [
        ("🪨", "Rock", "Common", 55),
        ("👟", "Old Shoe", "Common", 25),
        ("🦴", "Bone", "Uncommon", 12),
        ("🪙", "Old Coin", "Rare", 6),
        ("💎", "Shiny Gem", "Very Rare", 2),
    ]

    roll = random.uniform(0, 100)

    total = 0
    found = None

    for emoji, name, rarity, chance in loot_table:

        total += chance

        if roll <= total:
            found = (emoji, name, rarity)
            break

    # Safety fallback
    if found is None:
        found = loot_table[0][:3]

    emoji, item_name, rarity = found

    # -----------------------------------------
    # Add item to inventory
    # -----------------------------------------

    if item_name not in user["inventory"]:
        user["inventory"][item_name] = 0

    user["inventory"][item_name] += 1

    # Save cooldown timestamp
    user["last_dig"] = now

    save_data(data)

    # -----------------------------------------
    # Result
    # -----------------------------------------

    embed = discord.Embed(
        title="⛏️ Dig!",
        description=(
            f"You dug around in the **{user['location']}**...\n\n"
            f"**{emoji} {item_name}**\n"
            f"*{rarity}*"
        )
    )

    embed.set_footer(
        text="Something else might be hiding down there... 🐾"
    )

    await interaction.response.send_message(embed=embed)


# =========================================================
# RUN
# =========================================================

bot.run(TOKEN)
