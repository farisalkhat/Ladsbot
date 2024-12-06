import discord
from discord.ext import commands
import tokens
import getpass
USER_NAME = getpass.getuser()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.typing = True
intents.presences = True
intents.messages = True


api_key = tokens.discord_api

def get_prefix(bot, message):
    prefixes = ['!']
    # If bot is in DM, then they can only use commands starting with ?
    if not message.guild:
        return '?'
    return commands.when_mentioned_or(*prefixes)(bot, message)


initial_extensions = [ 'cogs.Dota']
bot = commands.Bot(command_prefix=get_prefix,
                   description='The Lads Dota Bot',intents=intents)
bot.remove_command('help')

        

@bot.event
async def on_ready():
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
    await bot.change_presence(activity=discord.Game(name='Dota 2', type=1))
    print(f'Successfully logged in and booted...!')

    if __name__ == '__main__':
        for extension in initial_extensions:
            await bot.load_extension(extension)
            print(extension)

bot.run(api_key, reconnect=True)


