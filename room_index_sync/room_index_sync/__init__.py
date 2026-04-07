from maubot import Plugin, MessageEvent
import asyncio

from mautrix.types import RoomID
from maubot.handlers import event, command
from mautrix.types import EventType


class RoomIndexSyncPlugin(Plugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task = None  # Background task placeholder

    async def start(self):
        """Start the recurring task when the bot starts."""
        self.task = self.loop.create_task(self.recurring_add_public_rooms())
        await self.task  # Wait for the task to complete (it won't, since it's an infinite loop)

    async def stop(self):
        """Cancel the task when the bot stops."""
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def recurring_add_public_rooms(self):
        """Fetch public rooms and add them to a space periodically."""
        space_id = RoomID("!JT44qByU_0o8ouHnxNCQatmdNe9jnO_ABHH-ZLppTeE")  # Replace with your space
        space_alias = RoomID("!JT44qByU_0o8ouHnxNCQatmdNe9jnO_ABHH-ZLppTeE")
        server = "nantral-platform.fr"               # Replace with the Synapse server
        limit = 200                         # Rooms per API page
        interval = 3600                     # Repeat every hour (in seconds)

        while True:
            # Get the rooms
            since = None
            rooms = []
            while True:
                res = await self.client.get_room_directory(limit=limit, since=since)
                since = res.get("next_batch")
                rooms.extend(res.get("chunk", []))
                if not since:
                    break

            self.log.info(f"Found {len(rooms)} rooms")

            # Add the rooms to the space if not already present
            for room in rooms:
                # ensures that we do not add the space to itself
                if space_id != room.get("room_id"):
                    await self.client.send_state_event(space_alias, EventType.SPACE_CHILD, state_key=room.get("room_id"), content={'via': [server]})
                    await asyncio.sleep(6) # avoid ratelimit (max 0.2/sec)

            self.log.info("All rooms added to space")

            await asyncio.sleep(interval)

    @command.new("invite_all_to")
    @command.argument("room_id")
    @command.argument("source_room")
    async def invite_all_to(self, evt: MessageEvent, room_id: RoomID, source_room: RoomID) -> None:
        await evt.reply(f"Inviting users from {source_room} -> {room_id}")

        try:
            members = await self.client.get_joined_members(source_room)
        except Exception as e:
            await evt.reply(f"Failed to fetch members: {e}")
            return

        invited = 0
        failed = 0

        for user_id in members:
            if user_id == self.client.mxid:
                continue

            try:
                await self.client.invite_user(room_id, user_id)
                invited += 1
                await asyncio.sleep(5)  # avoid rate limits
            except Exception as e:
                self.log.exception(f"Failed to invite user {user_id}: {e}")
                failed += 1

        await evt.reply(f"Invited {invited} users, failed to invite {failed} users.")
