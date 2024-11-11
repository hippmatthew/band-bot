import asyncio
import discord
import os
import random
from datetime import datetime
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
    self._ytdl_opts = { "format": "beataudio/best" }

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

  async def play(self, interaction: discord.Interaction, url: str, is_playlist: bool = False):
    if not await self._validate(interaction): return

    if not self._voice_client:
      await self.join(interaction)
    else:
      await interaction.response.defer( thinking = True )

    if is_playlist:
      try:
        info = await self.loop.run_in_executor(
          None,
          lambda: YoutubeDL(self._ytdl_opts).extract_info(url, download = False)
        )
      except Exception as e:
        await interaction.followup.send("Thats a whole lotta nothing")
        return
    else:
      try:
        info = YoutubeDL(self._ytdl_opts).extract_info(url, download = False )
      except Exception as e:
        await interaction.followup.send("I don't think that song is an actual song")
        return

    if not info:
      await interaction.followup.send("I don't know that tune")
      return

    if "entries" in info:
      for entry in info["entries"]:
        self._queue.add(
          Song(
            title       = entry["title"],
            url         = url,
            requester   = cast(discord.Member, interaction.user),
            stream      = entry["url"]
          )
        )
      await interaction.followup.send(f"Added {len(info['entries'])} songs to queue")
    else:
      self._queue.add(
        Song(
          title       = info["title"],
          url         = url,
          requester   = cast(discord.Member, interaction.user),
          stream      = info["url"]
        )
      )
      await interaction.followup.send(f"Added to queue: {info["title"]}")

    if not self._voice_client.is_playing():
      await self._play_next(interaction, None)

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
    if not await self._validate(interaction): return

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

  async def _play_next(self, interaction: discord.Interaction, prev_song: Optional[Song]):
    if self._queue.empty(): return
    if not self._voice_client: return

    song = prev_song if prev_song else self._queue.next()

    embed=discord.Embed(title=f"Up Next: {song.title}", description=f"requested by: {song.requester.mention}", color=discord.Color.dark_gold(), url=song.url)
    await interaction.followup.send(embed=embed)

    stream = "rickroll.mp4a" if random.randint(1, 100) == 69 else song.stream

    self._voice_client.play(
      discord.FFmpegPCMAudio( stream, options = "-vn" ),
      after = lambda e: asyncio.run_coroutine_threadsafe(
        self._play_next(interaction, song if self._is_looping else None),
        self.loop
      )
    )