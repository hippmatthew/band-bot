import asyncio
import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
from song_queue import SongQueue
from yt_dlp import YoutubeDL

load_dotenv( dotenv_path = Path('./.env') )

DISC_TOKEN = os.getenv('DISC_TOKEN')
if not DISC_TOKEN:
  raise SystemExit('failed to get discord token')

ydl_opts = { 'format': 'bestaudio' }

band_bot = commands.Bot( command_prefix = '/', intents = discord.Intents.all() )
songs = SongQueue()

@band_bot.event
async def on_ready():
  await band_bot.tree.sync()
  print(f'Logged in as {band_bot.user}')

@band_bot.tree.command( name = 'join', description = 'band bot joins a voice channel' )
async def join(ctx):
  if not ctx.author.voice:
    await ctx.send(f'{ctx.author.voice.channel} ain\'t no bandstand!')
    return

  channel = ctx.author.voice.channel
  await channel.connect()
  await ctx.send(f'I\'m performing at the {channel}')

  return ctx.voice_client

@band_bot.tree.command( name = 'leave', description = 'band bot leaves a voice channel' )
async def leave(ctx):
  if not ctx.voice_client: return

  await ctx.voice_client.disconnect()
  await ctx.send("I'm taking a break")

@band_bot.tree.command( name = 'request', description = 'band bot accepts your music request' )
async def request(ctx, *, search: str):
  voice = ctx.voice_client

  if not voice:
    if not ctx.author.voice: return
    voice = await ctx.author.voice.channel.connect()

  with YoutubeDL(ydl_opts) as ydl:
    try:
      info = ydl.extract_info( search, download = False )
    except Exception:
      await ctx.send("Not sure I know this one. Check the url you gave me or give me better search terms")
      return

    if not info:
      await ctx.send('Not sure I\'m understanding what you want me to play')
      return

    if 'entries' in info:
      for entry in info['entries']:
        url = entry['formats'][0]['url']
        songs.add(url)
      await ctx.send(f'I\'ll play those {len(info['entries'])} jams for you')
    else:
      url = info['formats'][0]['url']
      songs.add(url)
      await ctx.send(f'Sure! I\'ll play {info['title']} for you')

  if not voice.is_playing():
    await play_next(ctx, voice)

@band_bot.tree.command( name = 'queue', description = 'band bot displays the song queue' )
async def queue(ctx):
  if not ctx.voice_client:
    await ctx.send('I\'m on break! Gimme something to play and I\'ll head to the bandstand')
    return

  num = 1
  for song in songs.urls:
    with YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info( song, download = False)
    title = info.get('title', 'Unknown') if info else 'Unknown'

    await ctx.send(f'{num}. {title}')

    num += 1

@band_bot.tree.command( name = 'skip', description = 'band bot skips the current song in the queue' )
async def skip(ctx):
  voice = ctx.voice_client

  if not voice:
    await ctx.send('I\'m on break! Gimme something to play and I\'ll head to the bandstand')
    return

  if not voice.is_playing():
    await ctx.send('I ain\'t playing nothing right now')
    return

  await ctx.send('Alright, Alright. I\'ll see what else there is to play')
  voice.stop()

@band_bot.tree.command( name = 'artist', description = 'band bot invites a new artist to the bandstand' )
@commands.has_permissions( manage_nicknames = True )
async def artist(ctx, *, new_name: str):
  try:
    await ctx.guild.me.edit( nick = new_name )
    await ctx.send(f'Welcome to the stage, {new_name}!')
  except discord.Forbidden:
    await ctx.send(f'You can\'t tell me which performer to invite')
  except Exception as e:
    await ctx.send(f'I would invite them to play, but I encountered the exception: {e}')

@band_bot.tree.command( name = 'clear', description = 'band bot clears the song queue' )
async def clear(ctx):
  voice = ctx.voice_client

  if not voice:
    await ctx.send('I\'m on break! Gimme something to play and I\'ll head to the bandstand')
    return

  songs.clear()

async def play_next(ctx, voice):
  if songs.empty():
    await voice.disconnect()
    return

  song = songs.next()

  with YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info( song, download = False )
  title = info.get('title', 'Unknown') if info else 'Unknown'

  await ctx.send(f'Next up: {title}')

  def after(error):
    if error:
      print(f'encountered error: {error}')

    future = play_next(ctx, voice)
    future = asyncio.run_coroutine_threadsafe(future, band_bot.loop)

    try:
      future.result()
    except Exception as e:
      print(f'failed to play next song with exception: {e}')

  voice.play(discord.FFmpegPCMAudio( song, options = '-vn' ), after)

band_bot.run(DISC_TOKEN)