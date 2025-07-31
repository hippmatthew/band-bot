import os
from bot import Bot
from discord import Interaction

_DISC_TOKEN: str | None = os.getenv('DISC_TOKEN')
if not _DISC_TOKEN: raise SystemExit('failed to get discord token')

_BAND_BOT: Bot = Bot()

@_BAND_BOT.event
async def on_ready():
  await _BAND_BOT.tree.sync()
  print(f'beating meat as {_BAND_BOT.user}')

@_BAND_BOT.tree.command( name = 'join', description = 'band bot joins your channel' )
async def join(interaction: Interaction):
  await _BAND_BOT.join(interaction)

@_BAND_BOT.tree.command( name = 'leave', description = 'band bot leaves your channel and clears the queue')
async def leave(interaction: Interaction):
  await _BAND_BOT.leave(interaction)

@_BAND_BOT.tree.command( name = 'play', description = 'band bot queues up your song' )
async def play(interaction: Interaction, *, url: str):
  await _BAND_BOT.play(interaction, url)

@_BAND_BOT.tree.command( name = 'play_jazz_bar_classics', description = 'band bot plays jazz bar classics' )
async def play_jbc(interaction: Interaction):
  await _BAND_BOT.play_jbc(interaction)

@_BAND_BOT.tree.command( name = 'play_jazz_bar_masterpieces', description = 'band bot plays jazz bar masterpieces' )
async def play_jbc2(interaction: Interaction):
  await _BAND_BOT.play_jbc2(interaction)

@_BAND_BOT.tree.command( name = 'skip', description = 'band bot skips the current song' )
async def skip(interaction: Interaction):
  await _BAND_BOT.skip(interaction)

@_BAND_BOT.tree.command( name = 'loop', description = 'band bot loops the current song' )
async def loop(interaction: Interaction):
  await _BAND_BOT.toggle_loop(interaction)

_BAND_BOT.run(_DISC_TOKEN)