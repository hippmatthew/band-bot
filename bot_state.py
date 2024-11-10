import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, cast

load_dotenv( dotenv_path = Path("./.env") )

GUILD_ID = os.getenv( "GUILD_ID" )
if not GUILD_ID:
  raise SystemExit("failed to get GUILD_ID environment variable")
GUILD_ID = int(GUILD_ID)

class Song:
  def __init__(self, url: str, title: str):
    self.url = url,
    self.title = title,
    self.filename = title.replace(" ", "_")

class BotState:
  def __init__(self):
    self.bot = commands.Bot( command_prefix = "/", intents = discord.Intents.all() )
    self.voice_client: Optional[discord.VoiceClient] = None
    self.queue: list[Song] = []

  async def validate(self, interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member):
      await interaction.response.send_message("This ain't no bandstand!")
      return

    if not interaction.user.guild.id == GUILD_ID:
      await interaction.response.send_message(
        "BandBot is designed for a single server only. Please uninstall this bot immediately"
      )
      return

    if not interaction.user.voice:
      await interaction.response.send_message("You ain't even at the venue!")
      return

    if not interaction.user.voice.channel:
      await interaction.response.send_message("You ain't even at the venue!")
      return

  async def connect(self, interaction: discord.Interaction):
    if not self.validate(interaction): return