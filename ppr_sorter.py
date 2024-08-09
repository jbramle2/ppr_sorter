import discord
from discord.ext import commands
from discord import app_commands
from return_sort_ppr import *

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(
    command_prefix='!',
    test_guilds=[192460940409700352],
    sync_commands_debug=True,
    intents=intents
)
with open('token.txt', 'r') as t:
    discordtoken = t.read()


@bot.event
async def on_ready():
    print("Bot is online")  # Make sure it's on


@bot.event
async def on_raw_reaction_add(payload):
    if str(payload.emoji) == '⚖️':
        channel = bot.get_channel(payload.channel_id)  # Get the channel object
        message = await channel.fetch_message(payload.message_id)  # Fetch the message object

        players = await get_players(message)

        for x in range(len(players)):
            ppr = await get_player_ppr(players[x][1])
            players[x].append(ppr)
            print(ppr)

        sorted_list = sorted(players, key=lambda x: x[2], reverse=True)

        list1, list2 = find_best_split(sorted_list)

        avg_ppr_list1 = average_ppr(list1)
        avg_ppr_list2 = average_ppr(list2)

        formatted_list1 = format_ppr_list(list1)
        formatted_list2 = format_ppr_list(list2)

        await channel.send("Suggested Teams: \n" + '```Red  [' + str(round(avg_ppr_list1, 2)) + ']: ' + formatted_list1
                           + "\n" + 'Blue [' + str(round(avg_ppr_list2, 2)) + ']: ' + formatted_list2 + "```")

        await bot.process_commands(message)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if "The elim pickup has started" in message.content:
        # Add a reaction to the message
        emoji = "⚖️"
        await message.add_reaction(emoji)


@bot.tree.command(name="linkdiscord", description="linkdiscord", guild=discord.Object(id=192460940409700352))
@app_commands.checks.has_permissions(manage_channels=True)
async def linkdiscord(interaction: discord.Interaction, ut_name: str, ut_id: str, discord_id: str):

    message = await insert_update(ut_name, ut_id, discord_id)
    await interaction.response.send_message(message)


@bot.tree.command(name="deldiscordid", description="deldiscordid", guild=discord.Object(id=192460940409700352))
@app_commands.checks.has_permissions(manage_channels=True)
async def deldiscordid(interaction: discord.Interaction, discord_id: str):

    message = await remove_discord_id(discord_id)
    await interaction.response.send_message(message)

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}!')
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=192460940409700352))
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


bot.run(str(discordtoken))
