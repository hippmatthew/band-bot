import asyncio
import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, cast
from yt_dlp import YoutubeDL

from song_queue import SongQueue, Song

load_dotenv( dotenv_path = Path('./.env') )

GUILD_ID = os.getenv( "GUILD_ID" )
if not GUILD_ID:
  raise SystemExit("failed to get guild id")
GUILD_ID = int(GUILD_ID)

class Bot(commands.Bot):
  def __init__(self):
    self._voice_client: Optional[discord.VoiceClient] = None
    self._queue = SongQueue()
    self._is_looping = False

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

  async def play(self, interaction: discord.Interaction, url: str):
    if not await self._validate(interaction): return

    if not self._voice_client:
      await self.join(interaction)
      if not self._voice_client: return
    else:
      await interaction.response.defer()

    opts = {
      "format": "beataudio/best",
      "noplaylist": True
    }

    try:
      info = YoutubeDL(opts).extract_info(url, download = False )
    except Exception as e:
      await interaction.followup.send("I don't think that song is an actual song")
      return

    if not info:
      await interaction.followup.send("I don't know that tune")
      return

    song = Song(
      title = info["title"],
      url = url,
      requester = cast(discord.Member, interaction.user),
      stream = info["url"]
    )
    self._queue.add(song)
    await interaction.followup.send(f"Added to queue: {info["title"]}")

    if not self._voice_client.is_playing():
      await self._play_next(interaction, song)

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

  async def skip(self, interaction: discord.Interaction):
    if not self._validate(interaction): return

    if not self._voice_client:
      await interaction.response.send_message("I'm eating a sandwich right now. Call me later")
      return

    if not self._voice_client.is_playing():
      await interaction.response.send_message("I ain't even playing nothing")
      return

    await interaction.response.send_message("Fine. I'll play the next tune")
    self._voice_client.stop()

  def toggle_loop(self):
    self._is_looping = not self._is_looping

  async def _play_next(self, interaction, prev_song: Song):
    if self._queue.empty(): return
    if not self._voice_client: return

    song = prev_song if self._is_looping else self._queue.next()

    embed=discord.Embed(title=f"Up Next: {song.title}", description=f"requested by: {song.requester.mention}", color=discord.Color.dark_gold(), url=song.url)
    await interaction.followup.send(embed=embed)

    self._voice_client.play(
      discord.FFmpegPCMAudio( song.stream, options = "-vn" ),
      after = lambda e: asyncio.run_coroutine_threadsafe(self._play_next(interaction, song), self.loop)
    )