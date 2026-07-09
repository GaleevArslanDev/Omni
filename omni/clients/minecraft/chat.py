class ChatMixin:
    def say(self, text: str) -> None:
        self.bot.chat(text)
