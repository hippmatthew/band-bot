import asyncio
import discord
from discord.ext import commands
from discord.channel import VocalGuildChannel
from typing import Any, cast
from yt_dlp import YoutubeDL
from random import randint
from src.env import jbc_url, jbm_url
from src.song_queue import Song, SongQueue
from src.validation import validate_context, validate_interaction

_YTDLP_OPTS: dict[str, Any] = { "extract_flat": 'in_playlist', 'skip_download': True }
_FFMPEG_OPTS: str = '-vn'

async def setup(bot: commands.Bot):
  await bot.add_cog(MusicCog(bot))
  print('installed a music cog onto band bot')

class MusicCog(commands.Cog):
  queue: SongQueue
  __bot: commands.Bot
  __is_looping: bool
  __now_playing_msg: discord.Message | None

  def __init__(self, bot: commands.Bot) -> None:
    self.queue = SongQueue()
    self.__bot = bot
    self.__is_looping = False
    self.__now_playing_msg = None

  @commands.command()
  async def join(self, ctx: commands.Context) -> None:
    result: tuple[VocalGuildChannel, discord.Guild, discord.Member] | None = await validate_context(ctx)
    if not result: return
    channel, guild, _ = result

    if ctx.voice_client:
      await ctx.send('Fool, I\'m already playing somewhere else. Catch me after the show over here.')
      return

    await channel.connect()
    await ctx.send(f'I, {guild.me.display_name}, is performin at {channel.name}!')

  @commands.command()
  async def play(self, ctx: commands.Context, *, url: str):
    await self.__play_url(ctx, url)

  @commands.command()
  async def skip(self, ctx: commands.Context) -> None:
    result: tuple[VocalGuildChannel, discord.Guild, discord.Member] | None = await validate_context(ctx)
    if not result: return

    if not ctx.voice_client:
      await ctx.send('I\'m eating a sandwich right now. Call me later')
      return

    vc: discord.VoiceClient = cast(discord.VoiceClient, ctx.voice_client)

    if not vc.is_playing():
      await ctx.send('I ain\'t even playing nothing')
      return

    await ctx.send('Fine. I\'ll play the next tune')
    vc.stop()

  @commands.command()
  async def toggle_loop(self, ctx: commands.Context) -> None:
    result: tuple[VocalGuildChannel, discord.Guild, discord.Member] | None = await validate_context(ctx)
    if not result: return

    if not ctx.voice_client:
      await ctx.send('Fool, I ain\'t even playing nothin')
      return

    self.__is_looping = not self.__is_looping
    await ctx.send(
      'Guess I\'ll just play this song again and again and again until you tell me not to'
      if self.__is_looping else
      'Finally I can stop playing dat shit'
    )

  @commands.command(name = 'jazz_bar_classics')
  async def play_jbc(self, ctx: commands.Context) -> None:
    await self.__play_url(ctx, jbc_url())

  @commands.command(name = 'jazz_bar_masterpieces')
  async def play_jbm(self, ctx: commands.Context) -> None:
    await self.__play_url(ctx, jbm_url())

  @commands.command()
  async def leave(self, ctx: commands.Context) -> None:
    result: tuple[VocalGuildChannel, discord.Guild, discord.Member] | None = await validate_context(ctx)
    if not result: return

    if not ctx.voice_client:
      await ctx.send('I\'m already taking a break', ephemeral = True)
      return
    vc: discord.VoiceClient = cast(discord.VoiceClient, ctx.voice_client)

    await ctx.send('Call me back when ya need me')
    await vc.disconnect()

    self.__cleanup()

  async def skip_interaction(self, interaction: discord.Interaction) -> None:
    result: tuple[VocalGuildChannel, discord.Guild, discord.Member] | None = await validate_interaction(interaction)
    if not result: return
    _, guild, _ = result

    if not guild.voice_client:
      await interaction.response.send_message('I\'m eating a sandwich right now. Call me later', ephemeral = True)
      return
    vc: discord.VoiceClient = cast(discord.VoiceClient, guild.voice_client)

    if not vc.is_playing():
      await interaction.response.send_message('I ain\'t even playing nothing', ephemeral = True)
      return

    vc.stop()
    await interaction.response.send_message('Fine. I\'ll play the next tune')

  async def loop_interaction(self, interaction: discord.Interaction) -> None:
    result: tuple[VocalGuildChannel, discord.Guild, discord.Member] | None = await validate_interaction(interaction)
    if not result: return
    _, guild, _ = result

    if not guild.voice_client:
      await interaction.response.send_message('Fool, I ain\'t even playing nothin', ephemeral = True)
      return

    self.__is_looping = not self.__is_looping
    await interaction.response.send_message(
      'Guess I\'ll just play this song again and again and again until you tell me not to'
      if self.__is_looping else
      'Finally I can stop playing dat shit'
    )

  async def leave_interaction(self, interaction: discord.Interaction) -> None:
    result: tuple[VocalGuildChannel, discord.Guild, discord.Member] | None = await validate_interaction(interaction)
    if not result: return
    _, guild, _ = result

    if not guild.voice_client:
      await interaction.response.send_message('I\'m already taking a break', ephemeral = True)
      return
    vc: discord.VoiceClient = cast(discord.VoiceClient, guild.voice_client)

    await interaction.response.send_message('Call me back when ya need me')
    await vc.disconnect()

    self.__cleanup()

  async def __play_url(self, ctx: commands.Context, url: str) -> None:
    result: tuple[VocalGuildChannel, discord.Guild, discord.Member] | None = await validate_context(ctx)
    if not result: return
    channel, guild, requester = result

    if not ctx.voice_client:
      await channel.connect()
      await ctx.send(f'I, {guild.me.display_name}, is performin at {channel.name}!')

    vc: discord.VoiceClient = cast(discord.VoiceClient, ctx.voice_client)

    try:
      with YoutubeDL(_YTDLP_OPTS) as ytdlp:
        info: Any | dict[str, Any] | None = ytdlp.extract_info(url, download = False)
    except:
      await ctx.send('I don\'t think thats an actual tune. Gimme somethin real next time')
      return

    if not info:
      await ctx.send('Not sure I know dat one')
      return

    if 'entries' in info:
      for entry in info['entries']:
        self.queue.add(Song(
          title       = entry["title"],
          url         = entry['url'],
          requester   = requester,
          length      = entry["duration"],
        ))
      await ctx.send(
        f'Fine. I\'ll add those {info['playlist_count']} songs to the queue for ya.'
      )
    else:
      self.queue.add(Song(
        title       = info["title"],
        url         = url,
        requester   = requester,
        length      = info["duration_string"],
      ))
      await ctx.send(f'Yeah I know {info['title']}. I\'ll add it to the queue.')

    if not vc.is_playing():
      asyncio.run_coroutine_threadsafe(self.__play_next(ctx, self.queue.next()), self.__bot.loop)

  async def __play_next(self, ctx: commands.Context, song: Song | None) -> None:
    if not song or not ctx.voice_client: return
    vc: discord.VoiceClient = cast(discord.VoiceClient, ctx.voice_client)

    song.start_download()
    song.wait_for_stream()
    stream: str = song.stream if randint(1, 100) != 69 else '../rickroll.mp4a'

    if self.__now_playing_msg:
      await self.__now_playing_msg.delete()
      self.__now_playing_msg = None

    now_playing_embed: discord.Embed = discord.Embed(
      description = f'''
        ## <a:record:1305363860655444009> Now Playing
        [{song.title}]({song.url})
        {song.length}
        {song.requester.mention}
      ''',
      color = discord.Color.dark_gold(),
      url   = song.url
    )

    from src.views.now_playing import NowPlayingView
    self.__now_playing_msg = await ctx.send(embed = now_playing_embed, view = NowPlayingView(self))

    vc.play(
      discord.FFmpegPCMAudio(stream, options = _FFMPEG_OPTS),
      after = lambda _: asyncio.run_coroutine_threadsafe(
        self.__play_next(ctx, song if self.__is_looping else self.queue.next()),
        self.__bot.loop
      )
    )

  def __cleanup(self):
    self.queue.clear()
    self.queue.current_song = None
    self.__is_looping = False
