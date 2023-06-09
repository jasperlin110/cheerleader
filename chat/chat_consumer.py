from enum import StrEnum

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from chat.bots.utils import generate_bot


class ChatConsumer(AsyncJsonWebsocketConsumer):
    class MessageType(StrEnum):
        BOT_MESSAGE = "bot_message"
        CHAT_MESSAGE = "chat_message"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = generate_bot()

    async def connect(self):
        await self.accept()

    async def receive_json(self, content, **kwargs):
        message = content["data"]

        bot_message = self.bot.predict(
            user_message=message
        )

        await self.send_json({
            "type": self.MessageType.BOT_MESSAGE,
            "data": bot_message.strip()
        })
