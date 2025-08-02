import asyncio
import discord
from discord.ext import commands
from src.env import check_env, disc_token

_BAND_BOT: commands.Bot = commands.Bot(
  command_prefix  = commands.when_mentioned_or('/'),
  description     = 'The Jazz Lounge music bot',
  intents         = discord.Intents.all()
)

@_BAND_BOT.event
async def on_ready() -> None:
  print(f'beating meat as {_BAND_BOT.user}')

async def load_cogs() -> None:
  await _BAND_BOT.load_extension('src.cogs.music')

def print_commands() -> None:
  cogs: dict[str, list[str]] = {}
  for cmd in _BAND_BOT.commands:
    cogs[cmd.cog_name or 'No Cog'].append(cmd.name)

  print('\n=== registered commands ===')
  for cog in cogs:
    print(f'\n[{cog}]')
    for cmd in cog:
      print(f'\t{cmd}')

async def main() -> None:
  error_str: str = check_env()
  if error_str:
    raise SystemExit(f'errors in environment variables:{error_str}')

  async with _BAND_BOT:
    await load_cogs()
    print_commands()
    await _BAND_BOT.start(disc_token())

if __name__ == '__main__':
  asyncio.run(main())