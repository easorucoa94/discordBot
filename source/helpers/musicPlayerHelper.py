import yt_dlp
import urllib.request
import re

class musicPlayerHelper:
    @staticmethod
    def get_spotify_track_info(url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
            
            title_match = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html)
            desc_match = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html)
            
            title = title_match.group(1) if title_match else None
            desc = desc_match.group(1) if desc_match else None
            
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
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'cookiesfrombrowser': ('chrome',)
        }
        
        # Intercept Spotify URLs to extract track details and fallback to a YouTube search
        if "spotify.com" in url:
            search_query = musicPlayerHelper.get_spotify_track_info(url)
            if search_query:
                url = f"ytsearch1:{search_query}"
            # If scraping fails, we let yt-dlp try (it will raise a DRM error).

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                # Fallback for SoundCloud 404/API errors
                if "soundcloud.com" in url and "ytsearch" not in url:
                    # Extract a clean query from the URL path for scsearch
                    path_parts = [p for p in url.split("/") if p and "soundcloud.com" not in p and "http" not in p]
                    search_query = " ".join(path_parts).replace("-", " ")
                    if search_query:
                        info = ydl.extract_info(f"scsearch1:{search_query}", download=False)
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