import discord
from discord.ext import commands
from typing import Optional

class BandBot:
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.voice_client: Optional[discord.VoiceClient] = None

  def is_connected(self):
    return bool(self.voice_client)

  async def connect(self, channel):
    self.voice_client = await channel.connect()

  async def disconnect(self):
    if not self.voice_client: return

    await self.voice_client.disconnect()
    self.voice_client = None