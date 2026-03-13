import discord
from discord.ext import commands

# Load helpers
from helpers.musicPlayerHelper import musicPlayerHelper
from helpers.inactivityHelper import inactivityHelper

# Passing `name="..."` to commands.Cog changes the category name in the default help
class musicPlayerCommands(commands.Cog, name="Music Player"):
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    currentlyPlaying = False

    async def init(bot):
        await bot.add_cog(musicPlayerCommands(bot))

    async def isPlayingSong(self, ctx):
        if self.currentlyPlaying:
            await ctx.send("The bot is already playing a song.")
            return True
        return False

    def afterPlayingTrigger(self, error):
        self.currentlyPlaying = False
        if error:
            print(f'Player error: {error}')
        inactivityHelper.runInactivityTimer(self.guild)

    @commands.command(name="play")
    async def play(self, ctx, *, videoUrl):
        if not await self.isPlayingSong(ctx):
            if not ctx.message.author.voice:
                await ctx.send("You are not connected to a voice channel.")
                return
            else:
                channel = ctx.message.author.voice.channel

            if ctx.voice_client is None:
                await channel.connect()
            else:
                await ctx.voice_client.move_to(channel)

            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()

            self.guild = ctx.guild
            inactivityHelper.cancelTimer(self.guild)

            videoData = musicPlayerHelper.getVideoByUrl(videoUrl)
            audioStreamUrl = musicPlayerHelper.getAudioStreamUrl(videoData)
            
            playerData = discord.FFmpegPCMAudio(audioStreamUrl, **self.FFMPEG_OPTIONS)
            self.currentlyPlaying = True
            ctx.voice_client.play(playerData, after=self.afterPlayingTrigger)