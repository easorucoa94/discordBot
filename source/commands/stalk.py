import discord
from discord.ext import commands

from helpers.inactivityHelper import inactivityHelper

# Passing `name="..."` to commands.Cog changes the category name in the default help
class stalkCommands(commands.Cog, name="Stalk Commands"):
    stalkTarget = None
    
    async def init(bot):
        await bot.add_cog(stalkCommands(bot))

    async def stalkMember(self, member, voiceChannel):
        # We don't have ctx here, so we get the voice_client from the guild
        memberVoiceChannel = member.guild.voice_client
        
        if memberVoiceChannel is None:
            if voiceChannel.channel is not None:
                await voiceChannel.channel.connect()
        else:
            if voiceChannel.channel is not None:
                await memberVoiceChannel.move_to(voiceChannel.channel)
            else:
                await memberVoiceChannel.disconnect()

    @commands.command(name="stalk")
    async def stalk(self, ctx, *, stalkTarget):
        stalkTargetMemberObject = discord.utils.get(ctx.guild.members, global_name=stalkTarget)

        """
        if stalkTargetMemberObject.id == ctx.message.author.id:
            await ctx.send("You can't stalk yourself.")
            return
        """

        if stalkTargetMemberObject and stalkTargetMemberObject.id != self.stalkTarget:
            stalkMessage = f"Now stalking <@{stalkTargetMemberObject.id}>"
            if self.stalkTarget:
                stalkMessage = f"Stopped stalking <@{self.stalkTarget}> to stalk <@{stalkTargetMemberObject.id}> now"

            self.stalkTarget = stalkTargetMemberObject.id
            await ctx.send(stalkMessage)
            if stalkTargetMemberObject.voice is not None:
                await self.stalkMember(stalkTargetMemberObject, stalkTargetMemberObject.voice)
            else:
                inactivityHelper.runInactivityTimer(ctx.guild)
                
        elif stalkTargetMemberObject and stalkTargetMemberObject.id == self.stalkTarget:
            await ctx.send("Already stalking this user.")
        else:
            await ctx.send(f"Could not find user {stalkTarget}.")

    @commands.command(name="stopStalking")
    async def stopStalking(self, ctx):
        musicPlayerCog = ctx.bot.get_cog("Music Player")
        
        if ctx.voice_client and not musicPlayerCog.currentlyPlaying:
            await ctx.voice_client.disconnect()

        self.stalkTarget = None
        await ctx.send("Stopped stalking.")