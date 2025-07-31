import asyncio
import os
from discord import (
  VoiceClient, Intents, Interaction, Member, VoiceState,
  VoiceChannel, FFmpegPCMAudio, Color, Embed, Message
)
from discord.ext import commands
from typing import Any, cast
from song_queue import Song, SongQueue
from yt_dlp import YoutubeDL
from random import randint
from views import NowPlayingView

__GUILD_ID: str | None = os.getenv('GUILD_ID')
if not __GUILD_ID: raise SystemExit('failed to get guild id')

class Bot(commands.Bot):
  queue: SongQueue
  __voice_client: VoiceClient | None
  __is_looping: bool
  __ytdl_opts: dict[str, Any]
  __now_playing_msg_id: int | None

  def __init__(self) -> None:
    self.queue = SongQueue()
    self.__voice_client = None
    self.__ytdl_opts = { "extract_flat": 'in_playlist', 'skip_download': True }
    self.__is_looping = False
    self.__now_playing_msg_id = None

    super().__init__( command_prefix = '/', intents = Intents.all() )

  async def join(self, interaction: Interaction) -> None:
    if not await self.__validate(interaction): return

    user: Member = cast(Member, interaction.user)
    voice: VoiceState = cast(VoiceState, user.voice)
    channel: VoiceChannel = cast(VoiceChannel, voice.channel)

    if self.__voice_client and self.__voice_client.channel != channel:
      await self.__voice_client.move_to(channel)
    else:
      self.__voice_client = await channel.connect()

    await interaction.response.send_message(
      f'{self.__voice_client.user.name} is performing at {channel.name}'
    )

  async def leave(self, interaction: Interaction) -> None:
    if not self.__validate(interaction): return

    if not self.__voice_client:
      await interaction.response.send_message('I\'m already taking a break')
      return

    await interaction.response.send_message('Call me back when ya need me')
    await self.__voice_client.disconnect()

    self.__voice_client = None
    self.queue.clear()
    self.queue.current_song = None
    self.__is_looping = False
    self.__now_playing_msg_id = None

  async def play(self, interaction: Interaction, url: str) -> None:
    if not await self.__validate(interaction): return

    await interaction.response.defer( thinking = True )

    if not self.__voice_client:
      channel: VoiceChannel = cast(VoiceChannel, cast(VoiceState, cast(Member, interaction.user).voice).channel)
      self.__voice_client = await channel.connect()
      await interaction.followup.send(f'{self.__voice_client.user.name} is performing at {channel.name}')

    try:
      with YoutubeDL(self.__ytdl_opts) as ytdl:
        info: Any | dict[str, Any] | None = ytdl.extract_info(url, download = False)
    except:
      await interaction.followup.send('I don\'t think thats an actual tune. Gimme somethin real next time')
      return

    if not info:
      await interaction.followup.send('Not sure I know dat one')
      return

    if 'entries' in info:
      for entry in info['entries']:
        self.queue.add(Song(
          title       = entry["title"],
          url         = entry['url'],
          requester   = cast(Member, interaction.user),
          length      = entry["duration"],
        ))
      await interaction.followup.send(
        f'Fine. I\'ll add those {info['playlist_count']} songs to the queue for ya.'
      )
    else:
      self.queue.add(Song(
        title       = info["title"],
        url         = info['url'],
        requester   = cast(Member, interaction.user),
        length      = info["duration"],
      ))
      await interaction.followup.send(f'Yeah I know {info['title']}. I\'ll add it to the queue.')

    if not self.__voice_client.is_playing():
      asyncio.run_coroutine_threadsafe(self.__play_next(interaction, self.queue.next()), self.loop)

  async def skip(self, interaction: Interaction) -> None:
    if not await self.__validate(interaction): return

    if not self.__voice_client:
      await interaction.response.send_message('I\'m eating a sandwich right now. Call me later')
      return

    if not self.__voice_client.is_playing():
      await interaction.response.send_message('I ain\'t even playing nothing')
      return

    await interaction.response.send_message('Fine. I\'ll play the next tune')
    self.__voice_client.stop()

  async def toggle_loop(self, interaction: Interaction):
    self.__is_looping = not self.__is_looping
    await interaction.response.send_message(
      'Guess I\'ll just play this song again and again and again until you tell me not to'
      if self.__is_looping else
      'Finally I can stop playing dat shit'
    )

  async def play_jbc(self, interaction: Interaction):
    await self.play(interaction, 'https://www.youtube.com/watch?v=_sI_Ps7JSEk&t=7s')

  async def play_jbc2(self, interaction: Interaction):
    await self.play(interaction, 'https://www.youtube.com/watch?v=DpBWUv_91ho')

  async def __play_next(self, interaction: Interaction, song: Song | None) -> None:
    if not song or not self.__voice_client: return

    song.start_download()
    song.wait_for_stream()
    stream: str = song.stream if randint(1, 100) != 69 else '../rickroll.mp4a'

    if self.__now_playing_msg_id:
      await interaction.followup.delete_message(self.__now_playing_msg_id)

    now_playing_embed: Embed = Embed(
      description = f'''
        ## <a:record:1305363860655444009> Now Playing
        [{song.title}]({song.url})
        {song.length}
        {song.requester.mention}
      ''',
      color = Color.dark_gold(),
      url   = song.url
    )

    result: Message = await interaction.followup.send(
      embed = now_playing_embed, view = NowPlayingView(self), wait = True
    )
    self.__now_playing_msg_id = result.id

    self.__voice_client.play(
      FFmpegPCMAudio(stream, options = '-vn'),
      after = lambda _: asyncio.run_coroutine_threadsafe(
        self.__play_next(interaction, song if self.__is_looping else self.queue.next()),
        self.loop
      )
    )

  async def __validate(self, interaction: Interaction) -> bool:
    if not isinstance(interaction.user, Member):
      await interaction.response.send_message('Who da hell is dis? You ain\'t no member of da club.')
      return False

    if interaction.user.guild.id != 11111:
      await interaction.response.send_message('I only perform for one place and one place only. Get me outta here immediately.')
      return False

    if not interaction.user.voice:
      await interaction.response.send_message('You ain\'t even at the venue!')
      return False

    return True