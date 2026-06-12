import yt_dlp
import urllib.request
import re

class musicPlayerHelper:
    @staticmethod
    def getSpotifyTrackInfo(url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
            
            titleMatch = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html)
            descMatch = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html)
            
            title = titleMatch.group(1) if titleMatch else None
            desc = descMatch.group(1) if descMatch else None
            
            if not title:
                return None
                
            artist = ""
            if desc:
                parts = [p.strip() for p in desc.split('·')]
                if len(parts) > 1:
                    artist = parts[0]
                    
            return f"{title} {artist}".strip()
        except Exception:
            return None

    @staticmethod
    def getVideoByUrl(url):
        ydlOpts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'cookiesfrombrowser': ('chrome',)
        }
        
        # Intercept Spotify URLs to extract track details and fallback to a YouTube search
        if "spotify.com" in url:
            searchQuery = musicPlayerHelper.getSpotifyTrackInfo(url)
            if searchQuery:
                url = f"ytsearch1:{searchQuery}"
            # If scraping fails, we let yt-dlp try (it will raise a DRM error).

        with yt_dlp.YoutubeDL(ydlOpts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                # Fallback for SoundCloud 404/API errors
                if "soundcloud.com" in url and "ytsearch" not in url:
                    # Extract a clean query from the URL path for scsearch
                    pathParts = [p for p in url.split("/") if p and "soundcloud.com" not in p and "http" not in p]
                    searchQuery = " ".join(pathParts).replace("-", " ")
                    if searchQuery:
                        info = ydl.extract_info(f"scsearch1:{searchQuery}", download=False)
                    else:
                        raise e
                else:
                    raise e
                    
            if 'entries' in info:
                info = info['entries'][0]
            
            return info

    @staticmethod
    def getAudioStreamUrl(videoInfo):
        return videoInfo.get('url')