import asyncio
import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, cast
from yt_dlp import YoutubeDL

load_dotenv( dotenv_path = Path('./.env') )

GUILD_ID = os.getenv( "GUILD_ID" )
if not GUILD_ID:
  raise SystemExit("failed to get guild id")
GUILD_ID = int(GUILD_ID)

OUTPUT_PATH = os.getenv( "OUTPUT_PATH" )
if not OUTPUT_PATH:
  raise SystemExit("failed to get output path")

class Bot(commands.Bot):
  def __init__(self):
    self._voice_client: Optional[discord.VoiceClient] = None
    self._queue: list[tuple[str, str]] = []

    super().__init__( command_prefix = "/", intents = discord.Intents.all() )

  async def join(self, interaction: discord.Interaction):
    if not await self._validate(interaction): return

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

  async def leave(self, interaction: discord.Interaction):
    if not await self._validate(interaction): return

    if not self._voice_client:
      await interaction.response.send_message("I'm already on break!")
      return

    await self._voice_client.disconnect()
    await interaction.response.send_message("I'm taking a break!")

    self._voice_client = None

    with os.scandir(OUTPUT_PATH) as entries:
      for entry in entries:
        try:
          os.unlink(entry.path)
        except Exception as e:
          print(f'failed to remove file in queue directory with exception: {e}')

  async def play(self, interaction: discord.Interaction, url: str):
    if not await self._validate(interaction): return

    if not self._voice_client:
      await self.join(interaction)
      if not self._voice_client: return
    else:
      await interaction.response.defer()

    opts = {
      "format": "beataudio/best",
      "outtmpl": f"{OUTPUT_PATH}/%(title)s.mp4a",
      "noplaylist": True
    }

    try:
      info = YoutubeDL(opts).extract_info(url, download = True )
    except Exception as e:
      await interaction.followup.send("I don't think that song is an actual song")
      return

    if not info:
      await interaction.followup.send("I don't know that tune")
      return

    self._queue.append(( info["title"], f"{OUTPUT_PATH}/{info["title"]}.mp4a" ))
    await interaction.followup.send(f"Added to queue: {info["title"]}")

    if not self._voice_client.is_playing():
      await self._play_next(interaction)

  async def _validate(self, interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member):
      await interaction.response.send_message("This ain't no bandstand!")
      return False

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

  async def _play_next(self, interaction):
    if len(self._queue) == 0: return
    if not self._voice_client: return

    name, path = self._queue.pop(0)

    await interaction.followup.send(f"Up Next: {name}")

    self._voice_client.play(
      discord.FFmpegPCMAudio(path),
      after = lambda e: asyncio.run_coroutine_threadsafe(self._play_next(interaction), self.loop)
    )