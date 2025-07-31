import discord.ui
from discord import Interaction, ButtonStyle
from bot import Bot

class NowPlayingView(discord.ui.View):
  __bot: Bot

  def __init__(self, bot: Bot) -> None:
    super().__init__(timeout = None)
    self.__bot = bot

  @discord.ui.button(label='Queue', style=ButtonStyle.primary, custom_id='now_playing:queue', emoji='🎼')
  async def queue_button(self, interaction: Interaction, button: discord.ui.Button):
    await interaction.response.send_message(
      'Queue is empty' if self.__bot.queue.empty() else str(self.__bot.queue),
      ephemeral = True
    )

  @discord.ui.button(label='Skip', style=ButtonStyle.green, custom_id='now_playing:skip', emoji='⏩')
  async def skip_button(self, interaction: Interaction, button: discord.ui.Button):
    await self.__bot.skip(interaction)

  @discord.ui.button(label='Stop', style=ButtonStyle.red, custom_id='now_playing:stop', emoji='🛑')
  async def stop_button(self, interaction: Interaction, button: discord.ui.Button):
    await self.__bot.leave(interaction)