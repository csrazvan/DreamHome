from dataclasses import dataclass


@dataclass
class AppConfig:
    """
    App config:
    * id/key for TFL
    * slack token/channel where updates are sent to.
    """
    tfl_app_id: str
    tfl_app_key: str
    slack_token: str
    slack_channel: str
    db_name: str
