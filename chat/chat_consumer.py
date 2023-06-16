from enum import StrEnum

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings

from chat.bots.utils import generate_bot


class ChatConsumer(AsyncJsonWebsocketConsumer):
    class MessageType(StrEnum):
        BOT_MESSAGE = "bot_message"
        CHAT_MESSAGE = "chat_message"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = generate_bot()
        self.user_message_count = 0

    async def connect(self):
        await self.accept()

    async def receive_json(self, content, **kwargs):
        if content["type"] != self.MessageType.CHAT_MESSAGE:
            return

        self.user_message_count += 1
        if self.user_message_count > settings.MAX_USER_MESSAGE_COUNT:
            bot_message = f"You've reached your message limit! You can contact Jasper at {settings.EMAIL_ADDRESS} or " \
                          f"{settings.PHONE_NUMBER}."
        else:
            message = content["data"]
            bot_message = self.bot.predict(
                user_message=message
            )

        await self.send_json({
            "type": self.MessageType.BOT_MESSAGE,
            "data": bot_message.strip()
        })
