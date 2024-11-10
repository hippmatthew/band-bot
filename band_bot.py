import asyncio
import discord
import os
from connection import ConnectionManager
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
from song_queue import SongQueue
from yt_dlp import YoutubeDL

load_dotenv( dotenv_path = Path('./.env') )

DISC_TOKEN = os.getenv('DISC_TOKEN')
if not DISC_TOKEN:
  raise SystemExit('failed to get discord token')

OUTPUT_PATH = os.getenv('OUTPUT_PATH')
if not OUTPUT_PATH:
  raise SystemExit('failed to get output path')

band_bot = commands.Bot( command_prefix = '/', intents = discord.Intents.all() )
connection_manager = ConnectionManager()
songs = SongQueue()

@band_bot.event
async def on_ready():
  await band_bot.tree.sync()
  print(f'Logged in as {band_bot.user}')

@band_bot.tree.command( name = 'join', description = 'band bot joins a voice channel' )
async def join(interaction: discord.Interaction):
  if not isinstance(interaction.user, discord.Member):
    await interaction.response.send_message('I only perform on the big stage and this is definitely not that')
    return

  await connection_manager.connect(interaction, interaction.user)

@band_bot.tree.command( name = 'leave', description = 'band bot leaves a voice channel' )
async def leave(interaction: discord.Interaction):
  if not isinstance(interaction.user, discord.Member):
    await interaction.response.send_message('Don\'t tell me to get out when we\'re not even at a gig!')
    return

  await connection_manager.disconnect(interaction)

  with os.scandir(OUTPUT_PATH) as entries:
    for entry in entries:
      try:
        os.unlink(entry.path)
      except Exception as e:
        print(f'failed to remove file in queue directory with exception: {e}')

@band_bot.tree.command( name = 'play', description = 'band bot plays a YouTube song or playlist' )
async def play(interaction: discord.Interaction, *, url: str):
  if not isinstance(interaction.user, discord.Member):
    await interaction.response.send_message('We\'re not even at a venue. Don\'t ask me to play here')
    return

  if not connection_manager.voice_client:
    await connection_manager.connect(interaction, interaction.user)
    if not connection_manager.voice_client:
      await interaction.followup.send('Sorry, I cant make it right now')
      return

    await interaction.followup.send('I think I may know that one')
  else:
    await interaction.response.send_message('I think I may know that one')

  try:
    info = YoutubeDL().extract_info( url, download = False )
  except:
    await interaction.followup.send('Nevermind. Not sure that\'s an actual song')
    return

  if not info:
    await interaction.followup.send('Nah. I\'m not remembering it')
    return

  if 'entries' in info:
    for entry in info['entries']:
      print(f'entry url: {entry['formats'][0]['url']}')
      songs.add( entry['formats'][0]['url'], entry['title'] )
  else:
    print('not a playlist')
    songs.add( url, info['title'] )

  if songs.empty():
    await interaction.followup.send('Doesn\'t seem like you\'re asking me to play anything right now')
    return

  if not connection_manager.voice_client.is_playing():
    await play_next(interaction)

async def play_next(interaction: discord.Interaction):
  if songs.empty() or not connection_manager.voice_client: return

  url, title, filename = songs.next()

  opts = { 'format': 'bestaudio/best', 'outtmpl': f'{OUTPUT_PATH}/{filename}.mp4a' }
  YoutubeDL(opts).download(url)

  await interaction.followup.send(f'Next Up: {title}')

  connection_manager.voice_client.play(
    discord.FFmpegPCMAudio(f'{OUTPUT_PATH}/{filename}.mp4a'),
    after = lambda e: asyncio.run_coroutine_threadsafe(play_next(interaction), band_bot.loop)
  )

band_bot.run(DISC_TOKEN)