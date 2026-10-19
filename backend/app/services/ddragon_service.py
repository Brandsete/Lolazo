class DataDragonService:
    """Service to handle League of Legends Data Dragon CDN static assets."""

    DEFAULT_VERSION: str = "14.20.1"
    CDN_BASE: str = "https://ddragon.leagueoflegends.com/cdn"

    def __init__(self, version: str = DEFAULT_VERSION) -> None:
        self.version = version

    def get_profile_icon_url(self, icon_id: int) -> str:
        """Return the official Data Dragon CDN URL for a summoner profile icon."""
        return f"{self.CDN_BASE}/{self.version}/img/profileicon/{icon_id}.png"

    def get_champion_icon_url(self, champion_name: str) -> str:
        """Return the official Data Dragon CDN URL for a champion avatar."""
        return f"{self.CDN_BASE}/{self.version}/img/champion/{champion_name}.png"

    def get_item_icon_url(self, item_id: int) -> str:
        """Return the official Data Dragon CDN URL for an item icon."""
        return f"{self.CDN_BASE}/{self.version}/img/item/{item_id}.png"

    def get_spell_icon_url(self, spell_name: str) -> str:
        """Return the official Data Dragon CDN URL for a summoner spell."""
        return f"{self.CDN_BASE}/{self.version}/img/spell/{spell_name}.png"


ddragon_service = DataDragonService()
