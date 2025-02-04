from bot import Bot

import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path

load_dotenv( dotenv_path = Path("./.env") )

DISC_TOKEN = os.getenv( "DISC_TOKEN" )
if not DISC_TOKEN:
  raise SystemExit('failed to get discord token')

band_bot = Bot()

@band_bot.event
async def on_ready():
  await band_bot.tree.sync()
  print(f"beating meat as {band_bot.user}")

@band_bot.tree.command( name = "join", description = "band bot joins your channel" )
async def join(interaction: discord.Interaction):
  await band_bot.join(interaction)

@band_bot.tree.command( name = "leave", description = "band bot leaves your channel and clears the queue")
async def leave(interaction: discord.Interaction):
  await band_bot.leave(interaction)

@band_bot.tree.command( name = "play", description = "band bot queues up your song" )
async def play(interaction: discord.Interaction, *, url: str):
  await band_bot.play(interaction, url)

@band_bot.tree.command( name = "play_jazz_bar_classics", description = "band bot plays jazz bar classics" )
async def play_jbc(interaction: discord.Interaction):
  await band_bot.play_jbc(interaction)

@band_bot.tree.command( name = "play_jazz_bar_classics_2", description = "band bot plays jazz bar masterpieces" )
async def play_jbc2(interaction: discord.Interaction):
  await band_bot.play_jbc2(interaction)

@band_bot.tree.command( name = "skip", description = "band bot skips the current song" )
async def skip(interaction: discord.Interaction):
  await band_bot.skip(interaction)

@band_bot.tree.command( name = "loop", description = "band bot loops the current song" )
async def loop(interaction: discord.Interaction):
  band_bot.toggle_loop()
  await interaction.response.send_message(
    "Guess I'll just play this song again and again and again until you tell me not to"
  )

band_bot.run(DISC_TOKEN)