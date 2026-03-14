import asyncio
import os
import re
import aiohttp
import discord
from discord.ext import commands

MP3_MAGIC_BYTES = (b'\xff\xfb', b'\xff\xf3', b'\xff\xf2', b'ID3') ### VERIFY Bytes that are usually on MP3 for detecting malicious uploading
AUDIO_EXTENSION = '.mp3'
SOUNDS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'sounds'))
MAX_DOWNLOAD_BYTES = 10 * 1024 * 1024  # 10 MB, we can still change this for max size mp3
SAFE_NAME_RE = re.compile(r'^[\w\-]+$')  # letters, digits, underscores, hyphens

class soundboardCommands(commands.Cog, name="Soundboard"):
    FFMPEG_OPTIONS = {'options': '-vn'}  # -vn disables video

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        await self.session.close()

    @staticmethod
    async def init(bot):
        await bot.add_cog(soundboardCommands(bot))

    def _find_sound_file(self, name):
        path = os.path.join(SOUNDS_DIR, name + AUDIO_EXTENSION)
        return path if os.path.isfile(path) else None

    def _list_sounds(self):
        if not os.path.isdir(SOUNDS_DIR):
            return []
        return sorted(
            os.path.splitext(f)[0]
            for f in os.listdir(SOUNDS_DIR)
            if f.lower().endswith(AUDIO_EXTENSION)
        )

    @commands.group(name="sound", invoke_without_command=True)
    async def sound(self, ctx, *, query):
        if not ctx.message.author.voice:
            await ctx.send("You are not connected to a voice channel.")
            return

        query = query.strip()
        channel = ctx.message.author.voice.channel

        if ctx.voice_client is None:
            await channel.connect()
        else:
            await ctx.voice_client.move_to(channel)

        if ctx.voice_client.is_playing():
            await ctx.send("Already playing audio. Wait for it to finish.")
            return

        def after_playing(error):
            if error:
                print(f'Sound player error: {error}')
            asyncio.run_coroutine_threadsafe(ctx.voice_client.disconnect(), ctx.bot.loop)

        localFile = self._find_sound_file(query)
        if not localFile:
            await ctx.send(f"Sound `{query}` not found. Use `$sound list` to see available sounds.")
            return

        playerData = discord.FFmpegPCMAudio(localFile, **self.FFMPEG_OPTIONS)
        ctx.voice_client.play(playerData, after=after_playing)

    @sound.command(name="list")
    async def sound_list(self, ctx):
        sounds = self._list_sounds()
        if not sounds:
            await ctx.send("No sounds found in the sounds folder.")
            return
        formatted = "\n".join(f"• {name}" for name in sounds)
        await ctx.send(f"**Available sounds:**\n{formatted}")

    @sound.command(name="add")
    async def sound_add(self, ctx, url: str, name: str):
        if not url.lower().endswith(AUDIO_EXTENSION):
            await ctx.send(f"URL must end in `{AUDIO_EXTENSION}`.")
            return

        if not SAFE_NAME_RE.match(name):
            await ctx.send("Name can only contain letters, numbers, underscores, and hyphens.")
            return

        if self._find_sound_file(name):
            await ctx.send(f"`{name}` already exists. Choose a different name.")
            return

        os.makedirs(SOUNDS_DIR, exist_ok=True)
        
        destPath = os.path.join(SOUNDS_DIR, name + AUDIO_EXTENSION)

        await ctx.send(f"Downloading `{name}`...")
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    await ctx.send(f"Failed to download: HTTP {response.status}.")
                    return
                data = await response.content.read(MAX_DOWNLOAD_BYTES + 1)
        except aiohttp.ClientError as e:
            await ctx.send(f"Download error: {e}")
            return

        if len(data) > MAX_DOWNLOAD_BYTES:
            await ctx.send("File exceeds the 10 MB limit.")
            return

        if not any(data.startswith(magic) for magic in MP3_MAGIC_BYTES):
            await ctx.send("Que estas intentando mandar prro.")
            return

        with open(destPath, 'wb') as f:
            f.write(data)

        await ctx.send(f"Saved! Use `$sound {name}` to play it.")
