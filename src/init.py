import os
from bot import Bot
from discord import Interaction

__DISC_TOKEN: str | None = os.getenv('DISC_TOKEN')
if not __DISC_TOKEN: raise SystemExit('failed to get discord token')

__BAND_BOT: Bot = Bot()

@__BAND_BOT.event
async def on_ready():
  await __BAND_BOT.tree.sync()
  print(f'beating meat as {__BAND_BOT.user}')

@__BAND_BOT.tree.command( name = 'join', description = 'band bot joins your channel' )
async def join(interaction: Interaction):
  await __BAND_BOT.join(interaction)

@__BAND_BOT.tree.command( name = 'leave', description = 'band bot leaves your channel and clears the queue')
async def leave(interaction: Interaction):
  await __BAND_BOT.leave(interaction)

@__BAND_BOT.tree.command( name = 'play', description = 'band bot queues up your song' )
async def play(interaction: Interaction, *, url: str):
  await __BAND_BOT.play(interaction, url)

@__BAND_BOT.tree.command( name = 'play_jazz_bar_classics', description = 'band bot plays jazz bar classics' )
async def play_jbc(interaction: Interaction):
  await __BAND_BOT.play_jbc(interaction)

@__BAND_BOT.tree.command( name = 'play_jazz_bar_masterpieces', description = 'band bot plays jazz bar masterpieces' )
async def play_jbc2(interaction: Interaction):
  await __BAND_BOT.play_jbc2(interaction)

@__BAND_BOT.tree.command( name = 'skip', description = 'band bot skips the current song' )
async def skip(interaction: Interaction):
  await __BAND_BOT.skip(interaction)

@__BAND_BOT.tree.command( name = 'loop', description = 'band bot loops the current song' )
async def loop(interaction: Interaction):
  await __BAND_BOT.toggle_loop(interaction)

__BAND_BOT.run(__DISC_TOKEN)