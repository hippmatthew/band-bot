import discord
from discord.channel import VocalGuildChannel
from cogs.music import MusicCog
from validation import validate_interaction

class NowPlayingView(discord.ui.View):
  __music_cog: MusicCog

  def __init__(self, music_cog: MusicCog) -> None:
    super().__init__(timeout = None)
    self.__music_cog = music_cog

  @discord.ui.button(label='Queue', style=discord.ButtonStyle.primary, custom_id='now_playing:queue', emoji='🎼')
  async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
    result: tuple[VocalGuildChannel, discord.Guild, discord.Member] | None = await validate_interaction(interaction)
    if not result: return
    await interaction.response.send_message(
      'Queue is empty' if self.__music_cog.queue.empty() else str(self.__music_cog.queue),
      ephemeral = True
    )

  @discord.ui.button(label='Skip', style=discord.ButtonStyle.green, custom_id='now_playing:skip', emoji='⏩')
  async def skip_button(self, interaction: discord.Interaction, _: discord.ui.Button):
    await self.__music_cog.skip_interaction(interaction)

  @discord.ui.button(label='Loop', style=discord.ButtonStyle.gray, custom_id='now_playing:loop', emoji='')
  async def loop_button(self, interaction: discord.Interaction, _: discord.ui.Button):
    await self.__music_cog.loop_interaction(interaction)

  @discord.ui.button(label='Stop', style=discord.ButtonStyle.red, custom_id='now_playing:stop', emoji='🛑')
  async def stop_button(self, interaction: discord.Interaction, _: discord.ui.Button):
    await self.__music_cog.leave_interaction(interaction)