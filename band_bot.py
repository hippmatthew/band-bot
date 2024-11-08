import asyncio
import discord
import os
from bot import BandBot
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
from song_queue import SongQueue
from yt_dlp import YoutubeDL

load_dotenv( dotenv_path = Path('./.env') )

DISC_TOKEN = os.getenv('DISC_TOKEN')
if not DISC_TOKEN:
  raise SystemExit('failed to get discord token')

ydl_opts = {}

band_bot = BandBot(commands.Bot( command_prefix = '/', intents = discord.Intents.all() ))
songs = SongQueue()

@band_bot.bot.event
async def on_ready():
  await band_bot.bot.tree.sync()
  print(f'Logged in as {band_bot.bot.user}')

@band_bot.bot.tree.command( name = 'join', description = 'band bot joins a voice channel' )
async def join(interaction: discord.Interaction):
  if not isinstance(interaction.user, discord.Member):
    await interaction.response.send_message('I only perform on the big stage and this is definitely not that')
    return

  if band_bot.voice_client: return;

  if not interaction.user.voice:
    await interaction.response.send_message('This ain\'t no bandstand!')
    return

  channel = interaction.user.voice.channel
  if not channel: return

  await band_bot.connect(channel)
  await interaction.response.send_message(f'I\'m performing at the {channel}')

@band_bot.bot.tree.command( name = 'leave', description = 'band bot leaves a voice channel' )
async def leave(interaction: discord.Interaction):
  if not isinstance(interaction.user, discord.Member):
    await interaction.response.send_message('I only perform on the big stage and this is definitely not that')
    return

  if not band_bot.voice_client:
    await interaction.response.send_message("I\'m already on break! Just let me know when you want me to play again")
    return

  await band_bot.disconnect()
  await interaction.response.send_message("I'm taking a break")

@band_bot.bot.tree.command( name = 'request', description = 'band bot accepts your music request' )
async def request(interaction: discord.Interaction, *, search: str):
  if not isinstance(interaction.user, discord.Member):
    await interaction.response.send_message('I only perform on the big stage and this is definitely not that')
    return

  await interaction.response.defer()

  if not band_bot.voice_client:
    if not interaction.user.voice:
      await interaction.followup.send('This ain\'t no bandstand!')
      return

    channel = interaction.user.voice.channel
    if not channel: return

    await band_bot.connect(channel)
    if not band_bot.voice_client: return
    await interaction.followup.send(f'I\'m performing at the {channel}')

  with YoutubeDL(ydl_opts) as ydl:
    try:
      info = ydl.extract_info( search, download = False )
    except Exception:
      await interaction.followup.send(
        "Not sure I know this one. Check the url you gave me or give me better search terms"
      )
      return

    if not info:
      await interaction.followup.send('Not sure I\'m understanding what you want me to play')
      return

    if 'entries' in info:
      for entry in info['entries']:
        url = entry['formats'][0]['url']
        songs.add(url)
      await interaction.followup.send(f'I\'ll play those {len(info['entries'])} jams for you')
    else:
      url = info['formats'][0]['url']
      songs.add(url)
      await interaction.followup.send(f'Sure! I\'ll play {info['title']} for you')

  if not band_bot.voice_client.is_playing():
    await play_next(interaction)

@band_bot.bot.tree.command( name = 'queue', description = 'band bot displays the song queue' )
async def queue(interaction: discord.Interaction):
  if not isinstance(interaction.user, discord.Member):
    await interaction.response.send_message('I only perform on the big stage and this is definitely not that')
    return

  if not band_bot.voice_client:
    await interaction.response.send_message('I\'m on break! Gimme something to play and I\'ll head to the bandstand')
    return

  await interaction.response.defer()

  num = 1
  for song in songs.urls:
    with YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info( song, download = False )
    title = info.get('title', 'Unknown') if info else 'Unknown'

    await interaction.followup.send(f'{num}. {title}')

    num += 1

@band_bot.bot.tree.command( name = 'skip', description = 'band bot skips the current song in the queue' )
async def skip(interaction: discord.Interaction):
  if not isinstance(interaction.user, discord.Member):
    await interaction.response.send_message('I only perform on the big stage and this is definitely not that')
    return

  if not band_bot.voice_client:
    await interaction.response.send_message('I\'m on break! Gimme something to play and I\'ll head to the bandstand')
    return

  if not band_bot.voice_client.is_playing():
    await interaction.response.send_message('I ain\'t playing nothing right now')
    return

  await interaction.response.send_message('Alright, Alright. I\'ll see what else there is to play')
  band_bot.voice_client.stop()

@band_bot.bot.tree.command( name = 'artist', description = 'band bot invites a new artist to the bandstand' )
@commands.has_permissions( manage_nicknames = True )
async def artist(interaction: discord.Interaction, *, new_name: str):
  if not isinstance(interaction.user, discord.Member):
    await interaction.response.send_message('I only perform on the big stage and this is definitely not that')
    return

  if not interaction.guild: return

  try:
    await interaction.guild.me.edit( nick = new_name )
    await interaction.response.send_message(f'Welcome to the stage, {new_name}!')
  except discord.Forbidden:
    await interaction.response.send_message(f'You can\'t tell me which performer to invite')
  except Exception as e:
    await interaction.response.send_message(f'I would invite them to play, but I encountered the exception: {e}')

@band_bot.bot.tree.command( name = 'clear', description = 'band bot clears the song queue' )
async def clear(interaction: discord.Interaction):
  if not band_bot.voice_client:
    await interaction.response.send_message('I\'m on break! Gimme something to play and I\'ll head to the bandstand')
    return

  songs.clear()

async def play_next(interaction: discord.Interaction):
  if not band_bot.voice_client: return;

  if songs.empty():
    await band_bot.disconnect()
    return

  song = songs.next()

  with YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info( song, download = False )
  title = info.get('title', 'Unknown') if info else 'Unknown'

  def after(error):
    if error:
      print(f'encountered error: {error}')

    future = play_next(interaction)
    future = asyncio.run_coroutine_threadsafe(future, band_bot.bot.loop)

    try:
      future.result()
    except Exception as e:
      print(f'failed to play next song with exception: {e}')


  await interaction.followup.send(f'Next up: {title}')
  band_bot.voice_client.play(discord.FFmpegPCMAudio( song, options = '-vn' ), after = after)

band_bot.bot.run(DISC_TOKEN)