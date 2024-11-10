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
    self._bot = commands.Bot( command_prefix = "/", intents = discord.Intents.all() )
    self._voice_client: Optional[discord.VoiceClient] = None
    self._queue: list[Song] = []

  def run(self, token: str):
    self._bot.run(token)

  async def sync(self):
    await self._bot.tree.sync()
    print(f"logged in as {self._bot.user}")

  async def validate(self, interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member):
      await interaction.response.send_message("This ain't no bandstand!")
      return False

    print(f"guild id: {GUILD_ID}")
    print(f"user guild id: {interaction.user.guild.id}")

    if interaction.user.guild.id != GUILD_ID:
      await interaction.response.send_message(
        "BandBot is designed for a single server only. Please uninstall this bot immediately"
      )
      return False

    if not interaction.user.voice:
      await interaction.response.send_message("You ain't even at the venue!")
      return False

    if not interaction.user.voice.channel:
      await interaction.response.send_message("You ain't even at the venue!")
      return False

    return True

  async def connect(self, interaction: discord.Interaction):
    if not await self.validate(interaction): return

    user = cast(discord.Member, interaction.user)
    voice = cast(discord.VoiceState, user.voice)
    channel = cast(discord.VoiceChannel, voice.channel)

    if self._voice_client and self._voice_client.channel != channel:
      await self._voice_client.move_to(channel)
    else:
      self._voice_client = await channel.connect()

    await interaction.response.send_message(
      f"{self._voice_client.user.display_name} is performing at {channel.name}"
    )

  async def disconnect(self, interaction: discord.Interaction):
    if not await self.validate(interaction): return

    if not self._voice_client:
      await interaction.response.send_message("I'm already on break!")
      return

    await self._voice_client.disconnect()
    await interaction.response.send_message("I'm taking a break!")

    self._voice_client = None