import logging

import click
import yaml

from app import App
from app_config import AppConfig
from search_config import SearchConfig

LOGGER: logging.Logger = logging.getLogger()
handler = logging.FileHandler("dream_home.log")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
LOGGER.addHandler(handler)


@click.command()
@click.option("--tfl_app_id", help="TFP App ID")
@click.option("--tfl_app_key", help="TFP App Key")
@click.option("--slack_token", help="Slack token for your workspace")
@click.option("--slack_channel", help="Slack channel where the bot should post updates")
@click.option("--db_name", help="Name of sqlite db", default="dream_home.db")
@click.option("--debug", default=False, is_flag=True)
def run(tfl_app_id: str, tfl_app_key: str, slack_token: str, slack_channel: str, db_name: str, debug: bool):
    LOGGER.setLevel(logging.INFO)
    if debug:
        LOGGER.setLevel(logging.DEBUG)

    with open("config.yaml", "r") as f:
        data = yaml.safe_load(f)
        search_config = SearchConfig.from_dict(data)
    app_config = AppConfig(tfl_app_id, tfl_app_key, slack_token, slack_channel,db_name)

    App(app_config).search_properties(search_config)


if __name__ == '__main__':
    run()
