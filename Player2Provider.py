import json
import re
from bs4 import BeautifulSoup
from com.lagradost.cloudstream3 import (
    MainAPI,
    TvType,
    app,
)

class Player2Provider(MainAPI):
    def __init__(self):
        super().__init__()
        self.name = "Player 2 Provider"
        self.mainUrl = "https://coverapi.store"
        self.iconUrl = ""
        self.lang = "el"
        self.hasMainPage = False
        self.supportedTypes = {TvType.Movie, TvType.TvSeries}

    async def load(self, url: str):
        # Handles raw IMDb IDs (e.g. tt13684264) or full embed URLs
        if "tt" in url and not "http" in url:
            embed_url = f"https://coverapi.store/embed/{url}/"
        else:
            embed_url = url

        html = await app.get(embed_url)
        soup = BeautifulSoup(html.text, "html.parser")
        
        episodes = []

        # Scan script blocks for JSON configurations or stream playlists
        for script in soup.find_all("script"):
            script_text = script.text
            if "playlist" in script_text or "sources" in script_text:
                try:
                    start_idx = script_text.find("{")
                    end_idx = script_text.rfind("}") + 1
                    json_data = json.loads(script_text[start_idx:end_idx])
                    
                    playlist = json_data.get("playlist", [])
                    if len(playlist) > 1:
                        # Index 1 grabs Player 2 based on the tab order layout
                        player2_data = playlist[1]
                        ep_file = player2_data.get("file")
                        if ep_file:
                            episodes.append({
                                "name": "Player 2",
                                "data": ep_file,
                                "season": 1,
                                "episode": 1
                            })
                except Exception:
                    pass

        # Fallback: Extract all .m3u8 sources from the page and select the second one for Player 2
        if not episodes:
            m3u8_matches = re.findall(r'https?://[^\s<>"]+?\.m3u8[^\s<>"]*', html.text)
            unique_streams = list(dict.fromkeys(m3u8_matches))
            
            target_stream = unique_streams[1] if len(unique_streams) > 1 else (unique_streams[0] if unique_streams else embed_url)
            
            episodes.append({
                "name": "Player 2",
                "data": target_stream,
                "season": 1,
                "episode": 1
            })

        return {
            "name": f"Media {url}",
            "url": embed_url,
            "posterUrl": "",
            "tvType": TvType.TvSeries,
            "plot": "Loaded via Player 2 embed instance.",
            "episodes": episodes
        }

    async def load_links(self, data: str, is_movie: bool, subtitleCallback, callback) -> bool:
        if data and "http" in data:
            callback(
                {
                    "name": "Player 2",
                    "url": data,
                    "quality": 0,
                    "isM3u8": ".m3u8" in data,
                }
            )
            return True
            
        return False