import discord
from discord.ext import commands
from typing import Optional

class ConnectionManager:
  def __init__(self):
    self.voice_client: Optional[discord.VoiceClient] = None

  async def connect(self, interaction: discord.Interaction, member: discord.Member):
    if self.voice_client:
      await interaction.response.send_message('I\'m already on the bandstand!')
      return

    if not member.voice:
      await interaction.response.send_message('This ain\'t no bandstand!')
      return

    channel = member.voice.channel
    if not channel:
      await interaction.response.send_message('I cant make it to the venue right now')
      return

    self.voice_client = await channel.connect()
    await interaction.response.send_message(f'I\'m performing at the {channel}')

  async def disconnect(self, interaction: discord.Interaction):
    if not self.voice_client:
      await interaction.response.send_message("I\'m already on break! Just let me know when you want me to play again")
      return

    await self.voice_client.disconnect()
    await interaction.response.send_message("I'm taking a break")