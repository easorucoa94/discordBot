from discord.ext import commands

# Passing `name="..."` to commands.Cog changes the category name in the default help
class helpCommands(commands.Cog, name="General Commands"):
    async def init(bot):
        await bot.add_cog(helpCommands(bot))

    @commands.command(name="help")
    async def help(self, ctx):
        await ctx.send("```Help message```")