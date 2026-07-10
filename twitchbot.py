import os, django, asyncio, logging
from dotenv import load_dotenv

import twitchio
from twitchio import eventsub
from twitchio.ext import commands

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'streamToDo.settings')
django.setup()
from todos.models import StreamerProfile, TodoItem, TodoList
from allauth.socialaccount.models import SocialToken
from asgiref.sync import sync_to_async

load_dotenv()

LOGGER: logging.Logger = logging.getLogger("Bot")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
BOT_ID = os.getenv("BOT_ID")
OWNER_ID = os.getenv("OWNER_ID")

class Bot(commands.AutoBot):
    def __init__(self, *, subs: list[eventsub.SubscriptionPayload]) -> None:

        super().__init__(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=BOT_ID,
            owner_id=OWNER_ID,
            prefix="!",
            subscriptions=subs,
            force_subscribe=True,
        )
    
    async def setup_hook(self) -> None:
        await self.add_component(mainComp(self))

    async def add_token(self, token: str, refresh: str) -> twitchio.authentication.ValidateTokenPayload:
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(token, refresh)
        print(resp)
        return resp

    async def event_ready(self) -> None:
        LOGGER.info("Successfully logged in as: %s", self.bot_id)


class mainComp(commands.Component):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.command()
    async def hi(self, ctx:commands.Context) -> None:
        await ctx.reply(f"ello {ctx.chatter}! :3")


async def start_db() -> tuple[list[tuple[str, str]], list[eventsub.SubscriptionPayload]]:
    tokens: list[tuple[str, str]] = []
    subs: list[eventsub.SubscriptionPayload] = []
    
    def fetch_channels():
        return list(SocialToken.objects.select_related('account').all())

    channels = await sync_to_async(fetch_channels, thread_sensitive=True)()
    for channel in channels:
        tokens.append((channel.token, channel.token_secret))
        if channel.account.uid == BOT_ID:
            continue
        subs.extend([eventsub.ChatMessageSubscription(broadcaster_user_id=channel.account.uid, user_id=BOT_ID)])
    
    return tokens, subs


def main() -> None:
    twitchio.utils.setup_logging(level=logging.INFO)
    
    async def runner() -> None:
        tokens, subs = await start_db()

        async with Bot(subs=subs) as bot:
            for pair in tokens:
                await bot.add_token(*pair)
            
            await bot.start(load_tokens=False, with_adapter=False)

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Keyboardinterrupt, Shutting down Bot")



if __name__ == "__main__":
    main()