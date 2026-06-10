import discord
from discord.ext import commands
from collections import deque
import asyncio

# Load helpers
from helpers.musicPlayerHelper import musicPlayerHelper
from helpers.inactivityHelper import inactivityHelper

# Passing `name="..."` to commands.Cog changes the category name in the default help
class musicPlayerCommands(commands.Cog, name="Music Player"):
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.currentlyPlaying = {}
        self.currentSong = {}

    @classmethod
    async def init(cls, bot):
        await bot.add_cog(cls(bot))

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = deque()
        return self.queues[guild_id]

    def format_metadata(self, videoData, prefix="", queue_position=None):
        title = videoData.get('title', 'Unknown Title')
        uploader = videoData.get('uploader', videoData.get('artist', 'Unknown Artist'))
        extractor = videoData.get('extractor', 'Unknown Platform')
        webpage_url = videoData.get('webpage_url', videoData.get('url', 'No Link'))
        duration = videoData.get('duration', 0)
        
        mins, secs = divmod(duration, 60)
        duration_str = f"{mins}:{secs:02d}"
        
        position_str = f"\nQueue Position: {queue_position}" if queue_position is not None else ""
        
        return f"{prefix}\n```yaml\nTitle: {title}\nArtist: {uploader}\nPlatform: {extractor}\nDuration: {duration_str}\nLink: {webpage_url}{position_str}\n```"

    async def isPlayingSong(self, ctx):
        if self.currentlyPlaying.get(ctx.guild.id, False):
            await ctx.send("The bot is already playing a song.")
            return True
        return False

    def afterPlayingTrigger(self, error, ctx):
        self.currentlyPlaying[ctx.guild.id] = False
        self.currentSong[ctx.guild.id] = None
        if error:
            print(f'Player error: {error}')
        
        queue = self.get_queue(ctx.guild.id)
        if len(queue) > 0:
            videoData = queue.popleft()
            asyncio.run_coroutine_threadsafe(self.play_next_song(ctx, videoData), self.bot.loop)
        else:
            inactivityHelper.runInactivityTimer(ctx.guild)

    async def play_next_song(self, ctx, videoData):
        audioStreamUrl = musicPlayerHelper.getAudioStreamUrl(videoData)
        
        playerData = discord.FFmpegPCMAudio(audioStreamUrl, **self.FFMPEG_OPTIONS)
        self.currentlyPlaying[ctx.guild.id] = True
        self.currentSong[ctx.guild.id] = videoData
        ctx.voice_client.play(playerData, after=lambda e: self.afterPlayingTrigger(e, ctx))
        
        await ctx.send(self.format_metadata(videoData, "Now playing from queue:"))

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

        inactivityHelper.cancelTimer(ctx.guild)

        videoData = musicPlayerHelper.getVideoByUrl(videoUrl)
        audioStreamUrl = musicPlayerHelper.getAudioStreamUrl(videoData)

        if self.currentlyPlaying.get(ctx.guild.id, False) or ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            queue = self.get_queue(ctx.guild.id)
            queue.append(videoData)
            position = len(queue)
            await ctx.send(self.format_metadata(videoData, "Added to queue:", queue_position=position))
            return
        
        playerData = discord.FFmpegPCMAudio(audioStreamUrl, **self.FFMPEG_OPTIONS)
        self.currentlyPlaying[ctx.guild.id] = True
        self.currentSong[ctx.guild.id] = videoData
        ctx.voice_client.play(playerData, after=lambda e: self.afterPlayingTrigger(e, ctx))
        
        await ctx.send(self.format_metadata(videoData, "Now playing:"))

    @commands.command(name="skip")
    async def skip(self, ctx):
        if self.currentlyPlaying.get(ctx.guild.id, False) and ctx.voice_client is not None:
            ctx.voice_client.stop()
            await ctx.send("Skipped the current song.")
        else:
            await ctx.send("No music is currently playing.")

    @commands.command(name="queue")
    async def queue(self, ctx):
        queue_str = ""
        
        current_song = self.currentSong.get(ctx.guild.id)
        if self.currentlyPlaying.get(ctx.guild.id, False) and current_song:
            title = current_song.get('title', 'Unknown Title')
            duration = current_song.get('duration', 0)
            mins, secs = divmod(duration, 60)
            queue_str += f"**Now Playing:** {title} [{mins}:{secs:02d}]\n\n"

        queue = self.get_queue(ctx.guild.id)
        if len(queue) == 0:
            if not queue_str:
                await ctx.send("The queue is currently empty and nothing is playing.")
            else:
                queue_str += "**Upcoming Queue:**\nThe queue is empty."
                await ctx.send(queue_str)
            return

        queue_str += "**Upcoming Queue:**\n"
        for i, videoData in enumerate(queue):
            title = videoData.get('title', 'Unknown Title')
            duration = videoData.get('duration', 0)
            mins, secs = divmod(duration, 60)
            queue_str += f"{i + 1}. {title} [{mins}:{secs:02d}]\n"
            
            # Discord has a 2000 character limit per message
            if len(queue_str) > 1800:
                queue_str += f"...and {len(queue) - i - 1} more."
                break

        await ctx.send(queue_str)

    @commands.command(name="stop")
    async def stop(self, ctx):
        if ctx.guild.id in self.queues:
            self.queues[ctx.guild.id].clear()
            
        if self.currentlyPlaying.get(ctx.guild.id, False) and ctx.voice_client is not None:
            ctx.voice_client.stop()
            self.currentlyPlaying[ctx.guild.id] = False
            self.currentSong[ctx.guild.id] = None
            await ctx.send("Stopped playing music and cleared the queue.")
        else:
            await ctx.send("No music is currently playing.")