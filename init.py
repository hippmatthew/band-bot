from bot_state import BotState

import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path

load_dotenv( dotenv_path = Path("./.env") )

DISC_TOKEN = os.getenv( "DISC_TOKEN" )
if not DISC_TOKEN:
  raise SystemExit('failed to get discord token')

band_bot = BotState()

@band_bot._bot.event
async def on_ready():
  await band_bot.sync()

@band_bot._bot.tree.command( name = "join", description = "band bot joins your channel" )
async def join(interaction: discord.Interaction):
  await band_bot.connect(interaction)

@band_bot._bot.tree.command( name = "leave", description = "band bot leaves your channel" )
async def leave(interaction: discord.Interaction):
  await band_bot.disconnect(interaction)

@band_bot._bot.tree.command( name = "play", description = "band bot queues up your song" )
async def play(interaction: discord.Interaction, *, url: str):
  await band_bot.add_song(interaction, url)

@band_bot._bot.tree.command( name = "test", description = "test" )
async def test(interaction: discord.Interaction):
  file = open("./.env", "a")
  file.write(f"GUILD_ID='{interaction.guild_id}'")
  file.close()
  await interaction.response.send_message("meat beat")

band_bot.run(DISC_TOKEN)