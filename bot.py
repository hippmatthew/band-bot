import asyncio
import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
from random import randint
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
    self._ytdl_opts = { "extract_flat": 'in_playlist', "skip_download": True }
    self._now_playing_message_id: Optional[int] = None

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

    # cleanup
    await self._voice_client.disconnect()
    self._voice_client = None
    self._queue.clear()
    await interaction.response.send_message("I'm taking a break!")

    self._voice_client = None

  async def play(self, interaction: discord.Interaction, url: str):
    if not await self._validate(interaction): return

    if not self._voice_client:
      await self.join(interaction)
    else:
      await interaction.response.defer( thinking = True )

    try:
      info = YoutubeDL(self._ytdl_opts).extract_info(url, download = False )
    except:
      await interaction.followup.send("I don't think that song is an actual song")
      return

    if not info:
      await interaction.followup.send("I don't know that tune")
      return

    if 'entries' in info:
      for entry in info['entries']:
        song = Song(
          title       = entry["title"],
          url         = entry['url'],
          requester   = cast(discord.Member, interaction.user),
          length      = entry["duration"],
        )
        self._queue.add(song)

      await interaction.followup.send(f"Added {info['playlist_count']} songs to queue")
    else:
      song = Song(
        title       = info["title"],
        url         = url,
        requester   = cast(discord.Member, interaction.user),
        length      = info["duration_string"],
      )
      self._queue.add(song)

      add_to_queue_embed=discord.Embed(
        title=song.title,
        url=song.url,
        description=song.length
      )
      add_to_queue_embed.set_author(name="Added Song to Queue")
      await interaction.followup.send(embed=add_to_queue_embed)

    if not cast(discord.VoiceClient, self._voice_client).is_playing():
      song = self._queue.next()
      asyncio.run_coroutine_threadsafe(self._play_next(interaction, song), self.loop)

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

  async def play_jbc(self, interaction: discord.Interaction):
    await self.play(interaction, "https://www.youtube.com/watch?v=_sI_Ps7JSEk&t=7s")

  async def play_jbc2(self, interaction: discord.Interaction):
    await self.play(interaction, "https://www.youtube.com/watch?v=DpBWUv_91ho")

  async def _validate(self, interaction: discord.Interaction) -> bool:
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

  async def _play_next(self, interaction: discord.Interaction, song: Optional[Song]):
    print(f"queue is empty: {self._queue.empty()}")

    if not song: return
    if not self._voice_client: return

    song.start_download()
    song.wait_for_stream()
    stream = song.stream if randint(1, 100) != 69 else "rickroll.mp4a"

    now_playing_embed=discord.Embed(
      description=f"""
      ## <a:record:1305363860655444009> Now Playing
      [{song.title}]({song.url})
      {song.length}
      {song.requester.mention}
      """,
      color=discord.Color.dark_gold(), url=song.url
    )

    class NowPlayingView(discord.ui.View):
      def __init__(self, bot: Bot):
          super().__init__(timeout=None)
          self._bot = bot

      @discord.ui.button(label='Queue', style=discord.ButtonStyle.primary, custom_id='now_playing:queue', emoji='🎼')
      async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
          queue_str = self._bot._queue.print()
          if len(queue_str) == 0:
            queue_str = "Queue is empty!"
          await interaction.response.send_message(queue_str, ephemeral=True)

      @discord.ui.button(label='Skip', style=discord.ButtonStyle.green, custom_id='now_playing:skip', emoji='⏩')
      async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._bot.skip(interaction=interaction)

      @discord.ui.button(label='Stop', style=discord.ButtonStyle.red, custom_id='now_playing:stop', emoji='🛑')
      async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._bot.leave(interaction=interaction)

    if self._now_playing_message_id != None:
      await interaction.followup.delete_message(self._now_playing_message_id)
    result = await interaction.followup.send(embed=now_playing_embed, view=NowPlayingView(self))
    if not result:
      print("failed to get result from sending now playing embed")
      return
    self._now_playing_message_id = result.id

    self._voice_client.play(
      discord.FFmpegPCMAudio( stream, options = "-vn" ),
      after = lambda e: asyncio.run_coroutine_threadsafe(
        self._play_next(interaction, song if self._is_looping else self._queue.next()),
        self.loop
      )
    )