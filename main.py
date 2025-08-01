import asyncio
import discord
from discord.ext import commands
from src.cogs.music import MusicCog
from src.env import check_env, disc_token

_BAND_BOT: commands.Bot = commands.Bot(
  command_prefix  = commands.when_mentioned_or('/'),
  description     = 'The Jazz Lounge music bot',
  intents         = discord.Intents.all()
)

@_BAND_BOT.event
async def on_ready():
  print(f'beating meat as {_BAND_BOT.user}')

async def main():
  error_str: str = check_env()
  if error_str:
    raise SystemExit(f'errors in environment variables:{error_str}')

  async with _BAND_BOT:
    await _BAND_BOT.add_cog(MusicCog(_BAND_BOT))
    await _BAND_BOT.start(disc_token())

if __name__ == '__main__':
  asyncio.run(main())
