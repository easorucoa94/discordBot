import discord
from discord.ext import commands
from helpers.musicPlayerHelper import musicPlayerHelper

# Passing `name="..."` to commands.Cog changes the category name in the default help
class musicPlayerCommands(commands.Cog, name="Music Player"):
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    async def init(bot):
        await bot.add_cog(musicPlayerCommands(bot))

    @commands.command(name="play")
    async def play(self, ctx, *, videoUrl):
        if not ctx.message.author.voice:
            await ctx.send("You are not connected to a voice channel.")
            return
        else:
            channel = ctx.message.author.voice.channel

        if ctx.voice_client is None:
            await channel.connect()
        else:
            await ctx.voice_client.move_to(channel)

        videoData = musicPlayerHelper.getVideoByUrl(videoUrl)
        audioStreamUrl = musicPlayerHelper.getAudioStreamUrl(videoData)
        
        playerData = discord.FFmpegPCMAudio(audioStreamUrl, **self.FFMPEG_OPTIONS)
        
        ctx.voice_client.play(playerData, after=lambda e: print(f'Player error: {e}') if e else None)