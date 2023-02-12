import logging

from slack_sdk import WebClient

from property import Property


class Slack:
    """
    This class allows for sending messages/updates to slack.
    Currently it can send a notification about a newly discovered property that has a score about the notification
    treshold as well as sending individual messages.
    """

    def __init__(self, token: str, channel: str):
        self.slack_client = WebClient(token=token)
        self.channel = channel
        self.logger = logging.getLogger()

    def notify(self, target_property: Property, notify_at: int) -> bool:
        if target_property.score < notify_at:
            self.logger.info(
                f"Not going to notify for property {target_property.property_id} as its score {target_property.score} is less than threshold {notify_at}")
            return False

        self.logger.info(
            f"Sending notification for property {target_property.property_details.url} as score {target_property.score} greater than threshold {notify_at}")

        text = self.get_slack_notification_text(target_property)
        self.slack_client.chat_postMessage(channel=f"#{self.channel}",
                                           text=text,
                                           icon_emoji=':new:')

        self.slack_client.chat_postMessage(channel=f"#{self.channel}",
                                           text="-----------------------------------------",
                                           icon_emoji=':new:')
        return True

    def send_message(self, message: str) -> None:
        self.slack_client.chat_postMessage(channel=f"#{self.channel}",
                                           text=message,
                                           icon_emoji=':new:')

    def get_slack_notification_text(self, target_property: Property) -> str:
        property_details = target_property.property_details
        location = property_details.post_code if property_details.post_code else property_details.location
        text = ("""
            {title} - {url} - Score: {score}% 
            Location: {location}
            Price: {price} 
            Available from: {av}
            Bedrooms: {bedrooms} / Bathrooms: {bathrooms} 
            Garden: {has_garden}
            Broadband: {broadband}
            Description: ```{desc}```
            Score reasons: ```{score_reasons}```

            """
                ).format(
            location=location,
            url=property_details.url,
            price=property_details.price,
            desc=property_details.description[:1000],
            av=property_details.available_from,
            title=property_details.title,
            bedrooms=property_details.bedrooms,
            bathrooms=property_details.bathrooms,
            has_garden="With garden. " if property_details.has_garden else "No garden",
            score=target_property.score,
            broadband=f"https://www.openrent.co.uk/comparebroadband?postCode={property_details.post_code.replace(' ', '')}" if property_details.post_code else "Unknown broadband speeds",
            score_reasons="\n".join(target_property.score_reasons)
        )
        return text
