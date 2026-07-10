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
        await self.add_component(funCommands(self))
        await self.add_component(todoCommands(self))

    async def add_token(self, token: str, refresh: str) -> twitchio.authentication.ValidateTokenPayload:
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(token, refresh)
        return resp

    async def event_ready(self) -> None:
        LOGGER.info("Successfully logged in as: %s", self.bot_id)

@sync_to_async(thread_sensitive=True)
def fetch_profile(streamerName:str):
    return StreamerProfile.objects.get(twitch_username=streamerName)
@sync_to_async(thread_sensitive=True)
def fetch_profile_lists(profile:StreamerProfile):
    return profile.active_chat_list, profile.active_streamer_list
@sync_to_async(thread_sensitive=True)
def fetch_profile_limit(profile:StreamerProfile):
    return profile.max_viewer_todos
@sync_to_async
def fetch_list_items(todo_list:TodoList, filter:dict=None):
    if not filter:
        return list(todo_list.items.all())
    return list(todo_list.items.filter(**filter))


class funCommands(commands.Component):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.command()
    async def hi(self, ctx:commands.Context) -> None:
        await ctx.reply(f"ello {ctx.chatter}! :3")

class todoCommands(commands.Component):
    def __init__(self, bot:Bot):
        self.bot = bot

    @commands.group(invoke_fallback=True)
    async def todos(self, ctx:commands.Context) -> None:
        profile = await fetch_profile(ctx.broadcaster.name)
        chat_list, streamer_list = await fetch_profile_lists(profile)

        if not chat_list or not streamer_list:
            await ctx.send("Todos isn't fully setup at the moment! Let your streamer know so they can check it out!")
        else:
            await ctx.send("Use \"!todos add\", \"!todos list\", or \"!todos done\" to work with collaborative on stream Todo lists!")
    
    @todos.command(name="add", aliases=["make", "todo"])
    async def todos_add(self, ctx:commands.Context, *, title:str=None):
        profile = await fetch_profile(ctx.broadcaster.name)
        limit = await fetch_profile_limit(profile)
        chat_list, streamer_list = await fetch_profile_lists(profile)

        if not chat_list or not streamer_list:
            await ctx.send("Todos isn't fully setup at the moment! Let your streamer know so they can check it out!")
            return
        chatterItems = await fetch_list_items(chat_list, {"creator_name":ctx.chatter})
        if len(chatterItems) >= limit:
            await ctx.reply("You've reached the streamers limit for todos from a single chatter! Get something done before adding more!")
            return
        if not title:
            await ctx.reply("Please add a title for your todo!")
            return
        
        @sync_to_async(thread_sensitive=True)
        def save_new_item():
            newItem = TodoItem(todo_list=chat_list, creator_name=ctx.chatter, title=title)
            return newItem.save()
        chat_index = await save_new_item()

        await ctx.reply(f"Your todo has been added to the list! Use \"!todos done {chat_index}\" later on to mark it as done!")



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