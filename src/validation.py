import discord
from discord.ext import commands
from discord.channel import VocalGuildChannel
from env import guild_id, channel_id

async def validate_context(ctx: commands.Context) -> tuple[VocalGuildChannel, discord.Guild, discord.Member] | None:
  if not ctx.guild or not isinstance(ctx.author, discord.Member):
    await ctx.send('I dont do solo gigs. I only play on the bandstand.')
    return None

  if ctx.guild.id != guild_id():
    await ctx.send('I only perform for one venue and one venue only. Get me outta here ASAP')
    return None

  if not ctx.author.voice or not ctx.author.voice.channel:
    await ctx.send('Don\'t ask me to play if you ain\'t even at the venue!')
    return None

  if ctx.channel.id != channel_id():
    await ctx.send('Dis ain\'t the place for music, fool. Talk to me at the bandstand')
    return None

  return (ctx.author.voice.channel, ctx.guild, ctx.author)

async def validate_interaction(interaction: discord.Interaction) -> tuple[VocalGuildChannel, discord.Guild, discord.Member] | None:
  if not interaction.guild or not isinstance(interaction.user, discord.Member):
    await interaction.response.send_message('I dont do solo gigs. I only play on the bandstand.')
    return None

  if interaction.guild_id != guild_id():
    await interaction.response.send_message('I only perform for one venue and one venue only. Get me outta here ASAP')
    return None

  if not interaction.user.voice or not interaction.user.voice.channel:
    await interaction.response.send_message('Don\'t ask me to play if you ain\'t even at the venue!')
    return None

  if not interaction.channel or interaction.channel.id != channel_id():
    await interaction.response.send_message('Dis ain\'t the place for music, fool. Talk to me at the bandstand')
    return None

  return (interaction.user.voice.channel, interaction.guild, interaction.user)