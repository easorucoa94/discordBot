import discord
from discord.ext import commands

# Import commands
from commands.help import helpCommands
from commands.musicPlayer import musicPlayerCommands
from commands.stalk import stalkCommands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# We add `help_command=None` to disable the default discord.py help command.
# This prevents the `CommandRegistrationError` when we register our own help command.
bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)

@bot.event
async def setup_hook():
    # Load help commands
    await helpCommands.init(bot)
    # Load music player commands
    await musicPlayerCommands.init(bot)
    # Load stalk commands
    await stalkCommands.init(bot)

@bot.event
async def on_ready():
    if not discord.opus.is_loaded():
        # Homebrew on Apple Silicon usually puts libopus here
        discord.opus.load_opus('/opt/homebrew/Cellar/opus/1.6.1/lib/libopus.dylib')
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_voice_state_update(member, before, after):
    # Retrieve the Cog instance from the bot to get the updated instance variable
    stalkCog = bot.get_cog("Stalk Commands")
    currentStalkTarget = stalkCog.stalkTarget if stalkCog else None
    
    if currentStalkTarget == member.id:
        await stalkCommands.stalkMember(stalkCog, member, after)

@bot.event
async def on_message(message):
    # Don't respond to ourselves
    if message.author == bot.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    # Ensure other commands are processed
    await bot.process_commands(message)

# Run the bot
bot.run('TOKEN')