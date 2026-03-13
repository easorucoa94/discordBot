import yt_dlp

class musicPlayerHelper:
    @staticmethod
    def getVideoByUrl(url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'cookiesfrombrowser': ('chrome',)
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            
            return info

    def getAudioStreamUrl(videoInfo):
        return videoInfo.get('url')