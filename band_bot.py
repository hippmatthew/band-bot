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

@band_bot.tree.command( name = 'request', description = 'band bot takes your request' )
async def request(interaction: discord.Interaction, *, url: str):
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

  with YoutubeDL({}) as ydl:
    info = ydl.extract_info( url, download = False )

  if not info:
    await interaction.followup.send('Nah. I\'m not remembering it')
    return

  if 'entries' in info:
    for entry in info['entries']:
      songs.add( entry['formats'][0]['url'], entry['title'] )
  else:
    songs.add( url, info['title'] )

  if songs.empty():
    await interaction.followup.send('Doesn\'t seem like you\'re asking me to play anything right now')
    return

  if not connection_manager.voice_client or not connection_manager.voice_client.is_playing(): return

  while not songs.empty():
    if not connection_manager.voice_client: continue

    url, title, filename = songs.next()

    opts = { 'format': 'bestaudio/best', 'outtmpl': f'{OUTPUT_PATH}/{filename}.mp4a' }
    with YoutubeDL(opts) as ydl:
      ydl.download(url)

    await interaction.followup.send(f'Next Up: {title}')
    connection_manager.voice_client.play(discord.FFmpegPCMAudio(f'{OUTPUT_PATH}/{filename}.mp4a'))

@band_bot.tree.command( name = 'test', description = 'test' )
async def test(interaction: discord.Interaction):
  await interaction.response.send_message('testing audio')
  if not connection_manager.voice_client: return

  url = 'https://www.youtube.com/watch?v=po-0n1BKW2w'

  with YoutubeDL() as ydl:
    info = ydl.extract_info( url, download = False )
  if not info: return

  filename = info['title'].replace(' ', '_')
  opts = { 'format': 'bestaudio/best', 'outtmpl': f'{OUTPUT_PATH}/{filename}.mp4a' }

  with YoutubeDL(opts) as ydl:
    ydl.download(url)

  connection_manager.voice_client.play(discord.FFmpegPCMAudio(f'{OUTPUT_PATH}/{filename}.mp4a'))

band_bot.run(DISC_TOKEN)