import asyncio
import discord
from discord.ext import commands
from helpers.musicPlayerHelper import musicPlayerHelper

DIRECT_AUDIO_EXTENSIONS = ('.mp3', '.wav', '.ogg', '.flac', '.m4a', '.webm')

class soundboardCommands(commands.Cog, name="Soundboard"):
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    async def init(bot):
        await bot.add_cog(soundboardCommands(bot))

    @commands.command(name="sound")
    async def sound(self, ctx, *, query):
        if not ctx.message.author.voice:
            await ctx.send("You are not connected to a voice channel.")
            return

        channel = ctx.message.author.voice.channel

        if ctx.voice_client is None:
            await channel.connect()
        else:
            await ctx.voice_client.move_to(channel)

        # Direct audio URL — skip yt_dlp and stream it straight
        if query.startswith('http') and query.lower().endswith(DIRECT_AUDIO_EXTENSIONS):
            audioStreamUrl = query
        else:
            # If it's not a URL, treat it as a YouTube search query
            if not query.startswith('http'):
                query = f'ytsearch:{query}'
            videoData = musicPlayerHelper.getVideoByUrl(query)
            audioStreamUrl = musicPlayerHelper.getAudioStreamUrl(videoData)

        def after_playing(error):
            if error:
                print(f'Sound player error: {error}')
            asyncio.run_coroutine_threadsafe(ctx.voice_client.disconnect(), ctx.bot.loop)

        playerData = discord.FFmpegPCMAudio(audioStreamUrl, **self.FFMPEG_OPTIONS)
        ctx.voice_client.play(playerData, after=after_playing)
