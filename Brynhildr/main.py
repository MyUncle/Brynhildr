import asyncio
import discord
import dateparser
import datetime
import pytz
import requests

client = discord.Client()

ERRORMESSAGE = "Sorry, I couldn't understand that. Could you try again?"
MENTIONS = ("hey bryn", "hey brynhildr", "hey brynhild", "hi bryn",
            "hi brynhildr", "hi brynhild", "okay bryn", "okay brynhildr",
            "okay brynhild")
VERSION = "v1.02"
AVATAR = "https://cdn.discordapp.com/avatars/729790460175843368/c6c040e37004c" \
         "30ea82c1d3280792e98.png"
TOKEN = "NzI5NzkwNDYwMTc1ODQzMzY4.XwON_A.sXcW5jkXUSr3o3jvRTXXljBvZzg"


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))
    await client.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching,
                                  name="the stars"))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower().startswith(MENTIONS) or client.user in \
            message.mentions:
        if "remind me" in message.content.lower():
            await reminder(message.content.lower(), message)
        elif "remindme" in message.content.lower():
            await reminderstripped(message.content.lower(), message)
        elif "lookup" in message.content.lower():
            await lookupstripped(message.content, message)
        elif "help" in message.content.lower():
            await manual(message)
        elif "changelog" in message.content.lower():
            await changelog(message)
        elif "emotetest" in message.content.lower():
            await emotetest(message)


async def emotetest(message) -> None:
    await message.channel.send("\:despair:\:zeta:\:thinking:")


async def changelog(message) -> None:
    """
    Change log. Manually typed because file I/O is effort.
    """
    embed = discord.Embed()
    embed.title = "Change Log"
    embed.add_field(name="v1", value="- First operational build!\n- Supports "
                                     "basic GBF wiki lookup for weapons")
    embed.add_field(name="v1.01", value="- Added change log\n- Added warning "
                                        "for users attempting to set long "
                                        "reminders\n- Added help command "
                                        "functionality")
    embed.add_field(name="v1.01", value="- Fixed weapon lookups with edge cases"
                                        "\n- Minor help page reformatting")
    embed.set_footer(icon_url=AVATAR, text="Brynhildr " + VERSION +
                                           " | Made with ♥ by vicyush#4018")
    await message.channel.send(embed=embed)
    return


async def manual(message) -> None:
    """
    Help page. That's really it.
    """
    embed = discord.Embed()
    embed.set_footer(icon_url=AVATAR, text="Brynhildr " + VERSION +
                                           " | Made with ♥ by vicyush#4018")
    embed.set_author(name="Help")
    embed.add_field(name="Reminder", value="**@Brynhildr remindme [action] "
                                           "[time]** | Basic reminder function."
                                           " Warning: the bot is in active "
                                           "development and constant reboots "
                                           "mean that reminders over a longer "
                                           "time period may be lost.",
                    inline=False)
    embed.add_field(name="GBF Lookup", value="**@Brynhildr lookup [item]** | "
                                             "Lookup of pages from the GBF wiki"
                                             ". Currently, only weapon "
                                             "lookup is supported.",
                    inline=False)
    await message.channel.send(embed=embed)
    return


async def reminder(command: str, message) -> None:
    """
    Processes natural text-style input for the reminder function. Passes
    processed input to reminderoutput. Processing done by looking for specific
    strings in input. No machine learning here, just if statements (what's the
    difference?).
    Ideal format: Hey bot/[mention], remind me to [reminder] in/at [time]
    Key strings for processing (in required order):
    - Hey bot/[mention]
    - remind me to
    - in/at
    Time must be specified AFTER the reminder or else processing will not
    function properly. Error messages will be returned if input cannot be
    processed.
    """
    now = pytz.utc.localize(datetime.datetime.now())
    if "remind me to " in command:
        action = command.split("remind me to ", 1)[1]
    else:
        await message.channel.send(ERRORMESSAGE)
        return
    if action.rfind("in ") < 0 and action.rfind("at ") < 0:
        await message.channel.send(ERRORMESSAGE)
        return
    elif action.rfind("in ") > action.rfind("at "):
        endtime = dateparser.parse(action[action.rfind("in "):])
        if not endtime:
            await message.channel.send(ERRORMESSAGE)
            return
        delta = pytz.utc.localize(endtime) - now
        action = action[:action.rfind("in ")]
    else:
        endtime = dateparser.parse(action[action.rfind("at "):])
        if not endtime:
            await message.channel.send(ERRORMESSAGE)
            return
        delta = pytz.utc.localize(endtime) - now
        action = action[:action.rfind("at ")]
    await reminderoutput(action, delta, message)


async def reminderstripped(command: str, message) -> None:
    """
    Processes command-style input for the reminder function. Passes processed
    input to reminderoutput.
    Format: Hey bot/[mention] remindme "[reminder (in quotation marks)]" [time]
    """
    now = pytz.utc.localize(datetime.datetime.now())
    action = command.split("remindme ", 1)[1]
    date = action[action.rfind('"'):]
    if not date:
        await message.channel.send(ERRORMESSAGE)
        return
    action = action[1:action.rfind('"')]
    date = pytz.utc.localize(dateparser.parse(date))
    delta = now - date
    await reminderoutput(action + " ", delta, message)


async def reminderoutput(action: str, delta: datetime.timedelta, message) -> \
        None:
    if delta.days < 0 or delta.seconds < 0 or delta.microseconds < 0:
        await message.channel.send("The time you want is in the past. It's " +
                                   "too late for that now.")
        return
    times = [delta.days, delta.seconds // 3600, (delta.seconds // 60) % 60,
             delta.seconds % 60]
    units = [" days", " hours", " minutes", " seconds"]
    unitsused = sum(1 for x in times if x > 0)
    output = "Okay " + message.author.mention + ", I'll remind you to " + \
             action + "in "
    i = 0
    if unitsused == 1:
        while i < 5:
            if times[i] > 1:
                output += str(times[i]) + units[i] + "."
                break
            elif times[i] == 1:
                output += str(times[i]) + units[i][:-1] + "."
                break
            i += 1
    elif unitsused == 2:
        while unitsused > 1 and i < 5:
            if times[i] > 1:
                output += str(times[i]) + units[i]
                unitsused -= 1
            elif times[i] == 1:
                output += str(times[i]) + units[i][:-1]
                unitsused -= 1
            i += 1
        while unitsused == 1 and i < 5:
            if times[i] > 1:
                output += " and " + str(times[i]) + units[i] + "."
                break
            elif times[i] == 1:
                output += " and " + str(times[i]) + units[i][:-1] + "."
                break
            i += 1
    else:
        while unitsused > 1 and i < 5:
            if times[i] > 1:
                output += str(times[i]) + units[i] + ", "
                unitsused -= 1
            elif times[i] == 1:
                output += str(times[i]) + units[i][:-1] + ", "
                unitsused -= 1
            i += 1
        while unitsused == 1 and i < 5:
            if times[i] > 1:
                output += "and " + str(times[i]) + units[i] + "."
                break
            elif times[i] == 1:
                output += "and " + str(times[i]) + units[i][:-1] + "."
                break
            i += 1
    await message.channel.send(output)
    if delta.days > 0 or delta.seconds // 3600 > 1:
        await message.channel.send("Please be careful when asking for reminders"
                                   " over extended periods of time. The bot is "
                                   "in constant development and will reboot"
                                   "to implement new changes, losing any "
                                   "reminders that have been set.")
    await asyncio.sleep(delta.seconds + (delta.days * 86400))
    await message.channel.send(message.author.mention +
                               ", I'm reminding you to " + action +
                               "as you requested.")


async def lookupstripped(command: str, message) -> None:
    """
    Processes command-style input for the lookup function.
    Format: Hey bot/[mention] lookup [item]
    Currently not supporting lookup of Excalibur.
    """
    item = command[command.lower().rfind("lookup") + 7:]
    await lookupoutput(item, message)


async def lookupoutput(item: str, message) -> None:
    # Get a page with the given input
    url = "https://gbf.wiki/" + item.replace(" ", "_")
    page = requests.get(url)
    # Check if the input returns a valid page
    if "There is currently no text in this page." in page.text:
        await message.channel.send("Could not find this item. Search "
                                   "functionality will be added soon.")
        return
        # TODO: Add search functionality
        # page = requests.get("https://gbf.wiki/index.php?search=" +
        #                     item.replace(" ", "+"))
        # results = [i for i in range(len(page.text)) if page.text.startswith
        #            ("mw-search-result-heading", i)]
    # Get page categories
    categoryindex = page.text.find("wgCategories")
    # Move individual category parsing to a separate method in the future
    if "Weapons" not in page.text[categoryindex + 25:].split("]", 1)[0]:
        await message.channel.send("This is not a weapon page. I can't handle "
                                   "non-weapon pages right now.")
        return
    embed = discord.Embed()
    await weaponparse(page.text, embed)
    embed.title = page.text[page.text.find("wgTitle") + 10:].split('"', 1)[0]
    embed.url = url
    embed.set_author(name="GBF Wiki Lookup",
                     icon_url="https://gbf.wiki/images/1/18/Vyrnball.png?0704c")
    embed.set_footer(text="Brynhildr Bot is not associated with the GBF Wiki.")
    try:
        await message.channel.send(embed=embed)
    except:
        await message.channel.send("Something went wrong. Please let the bot"
                                   " owner know so this can be fixed.")


async def weaponparse(source: str, embed: discord.Embed) -> None:
    # Get description, and change apostrophe escape characters to actual
    # apostrophes
    description = source[source.find("meta name=\"description\" content=") +
                         33:].split('"', 1)[0].replace("&#039;", "'")
    if source.find("class=\"obtain-list-item\">") > 0:
        # Here's the headache...
        obtainraw = source[source.find("class=\"obtain-list-item\">") + 25:] \
                            .split("</td", 1)[0]
        # Remove tooltip spans
        while "<span class=\"tooltip\"" in obtainraw:
            obtainraw = obtainraw[:obtainraw.find("<span class=\"tooltip\"")] \
                        + obtainraw[obtainraw.find("</span>") + 7:]
            obtainraw = obtainraw[:obtainraw.find("</span>")] \
                        + obtainraw[obtainraw.find("</span>") + 7:]
        # If both images and image spans are in the remainder, remove the
        # first occurrence of either until there are no images left
        while "<span class=\"image_link\">" in obtainraw and \
              "<img" in obtainraw:
            if obtainraw.find("<span class=\"image_link\">") < \
               obtainraw.find("<img"):
                    obtainraw = obtainraw[:obtainraw.find
                                          ("<span class=\"image_link\">")] + \
                                obtainraw[obtainraw.find("/>") + 2:]
            else:
                obtainraw = obtainraw[:obtainraw.find("<img")] + \
                            obtainraw[obtainraw.find("/>") + 2:]
        # If there are image spans left over, remove them
        while "<span class=\"image_link\">" in obtainraw:
            obtainraw = obtainraw[:obtainraw.find
                                  ("<span class=\"image_link\">")] + \
                        obtainraw[obtainraw.find("/>") + 2:]
        # Remove this div because it breaks parsing
        while "<div class=\"obtain-list-item\">" in obtainraw:
            obtainraw = obtainraw[:obtainraw.find
                                  ("<div class=\"obtain-list-item\">")] + \
                                  obtainraw[obtainraw.find
                                            ("<div class=\"obtain-list-item\">")
                                            + 30:]
        # Hardcoded case because Arcarum creates an empty line.
        if "<a href=\"/Arcarum\" title=\"Arcarum\">" in obtainraw:
            obtainraw = obtainraw[:obtainraw.find
                                  ("<a href=\"/Arcarum\" title=\"Arcarum\">")] \
                        + obtainraw[obtainraw.find
                                    ("<a href=\"/Arcarum\" title=\"Arcarum\">")
                                    + 35:]
    else:
        obtainraw = source[source.find("class=\"obtain-list\">") + 20:] \
            .split("</td>", 1)[0]
    obtainlinks = [i for i in range(len(obtainraw)) if obtainraw.startswith
                   ("<a href=", i)]
    obtaintext = [i for i in range(len(obtainraw)) if obtainraw.startswith
                  ("\">", i)]
    index = 0
    while index < len(obtaintext) and obtaintext[index] < len(obtainraw):
        if obtainraw[obtaintext[index] + 2: obtaintext[index] + 6] == "<img":
            del obtainlinks[index]
            del obtaintext[index]
        index += 1
    obtain = ""
    i = 0
    while i < len(obtainlinks):
        obtain += ("[" + obtainraw[obtaintext[i] + 2:].split('<', 1)[0] +
                   "](https://gbf.wiki" +
                   obtainraw[obtainlinks[i] + 9:].split('"', 1)[0] + ")\n")
        i += 1
    image = source[source.find("flex-direction:row;\">") + 21:].split(
        "</a>", 1)[0]
    image = "https://gbf.wiki" + \
            image[image.find("/images/thumb"):].split('"', 1)[0]
    embed.description = description
    embed.set_thumbnail(url=image)
    embed.add_field(name="Obtain", value=obtain)


client.run(TOKEN)
