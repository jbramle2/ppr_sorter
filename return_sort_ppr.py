from itertools import combinations
import psycopg2
from psycopg2 import sql

with open('stats_pass.txt', 'r') as t:
    stats_pass = t.read()


async def get_players(message):
    found_names_with_ids = []

    # Create a dictionary mapping both display names and usernames to their IDs
    names_to_ids = {member.display_name: member.id for member in message.guild.members}
    names_to_ids.update({member.name: member.id for member in message.guild.members})
    names_to_ids.update({member.mention: member.id for member in message.guild.members})

    # Iterate over each word in the message
    for word in message.content.split():
        # Clean the word by removing leading and trailing punctuation
        print(f'word1: {word}')
        clean_word = word.strip('@,!?[]{}<:;"\'')
        # Needed to fully remove escaped characters
        clean_word = clean_word.replace('\\', '')

        print(f'word2: {clean_word}')

        # Check if the cleaned word is a display name or username in the server
        # If a word is a name, it appends it along with their discord id.
        if clean_word in names_to_ids:
            found_names_with_ids.append([clean_word, names_to_ids[clean_word]])

    print(found_names_with_ids)

    # Remove duplicates based on 2nd value of nested list
    unique_dict = {item[1]: item for item in found_names_with_ids}
    unique_list = list(unique_dict.values())

    # await bot.process_commands(message)
    return unique_list


# Finds a player by their discord id
async def get_player_ppr(player):

    conn_game = psycopg2.connect(
        host="104.153.105.63",
        database="utstats",
        user="readonly_user",
        password=stats_pass,
        port=5432)

    c2 = conn_game.cursor()

    c2.execute("SELECT playerid FROM utpugs_discordids WHERE discord_id = '" + str(player) + "' LIMIT 1")
    player_id = c2.fetchone()

    if player_id:
        print(player_id[0])
        c2.execute("SELECT ppr FROM pug_stats_limit_20 WHERE playerid_id = '" + str(player_id[0]) + "'")
        player_ppr = c2.fetchone()
        c2.close()
        print(player_ppr)
        return round(player_ppr[0], 2)


    else:
        c2.close()
        return 0


def find_best_split(nested_list):
    # Sort the list to optimize combination generation
    nested_list.sort(key=lambda x: x[2])

    total_sum = sum(item[2] for item in nested_list)
    closest_difference = total_sum
    best_split = None

    n = len(nested_list)

    # Ensure that the list has an even number of elements
    if n % 2 != 0:
        raise ValueError("The list must have an even number of elements.")

    # Generate combinations where both lists will have the same number of elements
    half_n = n // 2
    for combo in combinations(nested_list, half_n):
        combo_sum = sum(item[2] for item in combo)
        difference = abs(total_sum - 2 * combo_sum)

        if difference < closest_difference:
            closest_difference = difference
            best_split = combo

    # Divide the list into two based on the best split found
    list1 = list(best_split)
    list2 = [item for item in nested_list if item not in list1]

    return list1, list2


def average_ppr(nested_list):
    if not nested_list:
        return 0  # Return 0 or suitable value if the list is empty

    total_sum = sum(item[2] for item in nested_list)
    count = len(nested_list)
    average = total_sum / count
    return average


def format_ppr_list(nested_list):
    # Iterate through each sublist and format it as "first (third)"
    formatted_elements = [f"{item[0]} ({item[2]})" for item in nested_list]
    # Join all formatted elements into a single string
    return ', '.join(formatted_elements)

############################################################
# Adding, updating, and removing entries
############################################################
async def insert_update(ut_name, ut_id, discord_id):
    try:
        conn_game = psycopg2.connect(
            host="104.153.105.63",
            database="utstats",
            user="readonly_user",
            password=stats_pass,
            port=5432)

        c2 = conn_game.cursor()

        c2.execute("SELECT discord_id, playername FROM utpugs_discordids WHERE discord_id = '" + str(discord_id) + "'")
        discord_id_test = c2.fetchone()
        print(discord_id_test)
        c2.close()

        if len(discord_id) > 17 and len(ut_id) == 32 and discord_id_test is None:

            update_query = sql.SQL("""
                INSERT INTO public.utpugs_discordids (playername, playerid, discord_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (playerid) DO UPDATE
                SET playername = EXCLUDED.playername,
                    discord_id = EXCLUDED.discord_id
            """)

            updated_values = [ut_name, ut_id, discord_id]

            c2.execute(update_query, updated_values)
            conn_game.commit()

            return "Values inserted/updated: (" + ut_name + ", " + ut_id + ", " + discord_id + ")"
        elif discord_id:
            return ("Discord id is already in db as: " + str(discord_id_test[1]) +
                    ". Remove it (/deldiscordid) and retry")
        else:
            return "UT ID or Discord ID is invalid"

    except Exception as error:
        print(f"Error occurred: {error}")
        return str(error)

    finally:
        if conn_game is not None:
            c2.close()
            conn_game.close()
            print("PostgreSQL connection is closed.")


async def remove_discord_id(discord_id):
    try:
        conn_game = psycopg2.connect(
            host="104.153.105.63",
            database="utstats",
            user="readonly_user",
            password=stats_pass,
            port=5432)

        c2 = conn_game.cursor()

        print(len(discord_id))
        if len(discord_id) > 17 and discord_id.isnumeric():
            c2.execute("DELETE FROM utpugs_discordids WHERE discord_id = '" + str(discord_id) + "'")
            return discord_id + " removed"
        else:
            return discord_id + " is not a valid discord id"

        conn_game.commit()
        print("ID Deleted")

    except Exception as error:
        print(f"Error occurred: {error}")

    finally:
        if conn_game is not None:
            c2.close()
            conn_game.close()
            print("PostgreSQL connection is closed.")
