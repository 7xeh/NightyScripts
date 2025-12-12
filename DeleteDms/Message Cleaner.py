@nightyScript(
    name="Message Cleaner",
    author="7xeh",
    description="Delete your own Discord messages from servers, groups, or DMs with UI helpers and the dpm command.",
    usage="dpm <amount|all>"
)
def delete_personal_messages():
    import asyncio
    import json
    from datetime import datetime
    from pathlib import Path
    from typing import Optional, Tuple

    import discord

    SCRIPT_ID = "dpm"
    DEFAULT_LIMIT = 100
    MAX_LIMIT = 10000

    settings_path = Path(getScriptsPath()) / "json" / "delete_personal_messages_settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    def load_settings() -> dict:
        if not settings_path.exists():
            return {
                "channel_id": "",
                "dm_id": "",
                "group_id": "",
                "limit": str(DEFAULT_LIMIT),
                "delete_all": False,
            }
        try:
            with settings_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
                return {
                    "channel_id": str(data.get("channel_id", "")),
                    "dm_id": str(data.get("dm_id", "")),
                    "group_id": str(data.get("group_id", "")),
                    "limit": str(data.get("limit", DEFAULT_LIMIT)),
                    "delete_all": bool(data.get("delete_all", False)),
                }
        except (json.JSONDecodeError, OSError):
            return {
                "channel_id": "",
                "dm_id": "",
                "group_id": "",
                "limit": str(DEFAULT_LIMIT),
                "delete_all": False,
            }

    def save_settings(new_values: dict) -> None:
        current = load_settings()
        current.update(new_values)
        with settings_path.open("w", encoding="utf-8") as handle:
            json.dump(current, handle, indent=4)

    def parse_amount_argument(argument: str) -> Optional[int]:
        if not argument:
            return DEFAULT_LIMIT
        argument = argument.strip().lower()
        if argument in {"all", "*", "infinite"}:
            return None
        if not argument.isdigit():
            return DEFAULT_LIMIT
        value = int(argument)
        value = max(1, min(MAX_LIMIT, value))
        return value

    async def safe_fetch_channel(channel_id: int) -> Optional[discord.abc.Messageable]:
        channel = bot.get_channel(channel_id)
        if channel:
            return channel
        try:
            channel = await bot.fetch_channel(channel_id)
            return channel
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    async def resolve_dm_channel(user_id: int) -> Optional[discord.DMChannel]:
        user = bot.get_user(user_id)
        if not user:
            try:
                user = await bot.fetch_user(user_id)
            except (discord.NotFound, discord.HTTPException):
                return None
        if user.dm_channel:
            return user.dm_channel
        try:
            return await user.create_dm()
        except discord.HTTPException:
            return None

    async def purge_channel(
        channel: discord.abc.Messageable,
        limit: Optional[int],
        status_hook=None,
    ) -> Tuple[int, int]:
        deleted = 0
        scanned = 0
        before_message = None
        keep_running = True

        def report(message: str) -> None:
            if status_hook:
                status_hook(message)

        report("Collecting messages")
        while keep_running:
            batch = []
            try:
                async for message in channel.history(limit=100, before=before_message, oldest_first=False):
                    batch.append(message)
                    if len(batch) >= 100:
                        break
            except discord.Forbidden:
                report("Missing permissions to view history")
                break
            except discord.HTTPException as error:
                report(f"Discord error: {error}")
                await asyncio.sleep(1.5)
                continue

            if not batch:
                break

            for message in batch:
                scanned += 1
                before_message = message
                if message.author.id != bot.user.id:
                    continue
                try:
                    await message.delete()
                    deleted += 1
                    report(f"Deleted {deleted} • Scanned {scanned}")
                    await asyncio.sleep(0.35)
                except discord.HTTPException as error:
                    report(f"Failed to delete {message.id}: {error}")
                    await asyncio.sleep(1.5)
                if limit is not None and deleted >= limit:
                    keep_running = False
                    break

            await asyncio.sleep(0.5)

        report(f"Done • Deleted {deleted} of {scanned} scanned")
        return scanned, deleted

    async def run_ui_purge(channel_resolver, limit: Optional[int], origin_label: str, button_ref):
        if ui_state["running"]:
            cleaner_tab.toast(type="INFO", title="In Progress", description="A purge is already running.")
            return

        ui_state["running"] = True
        button_ref.loading = True
        update_status(f"Resolving {origin_label}…")

        try:
            channel = await channel_resolver()
            if not channel:
                update_status(f"Status: Could not locate {origin_label}.")
                cleaner_tab.toast(type="ERROR", title="Invalid Target", description=f"Unable to open {origin_label}.")
                return

            async def hook(message: str):
                update_status(f"{origin_label}: {message}")

            scanned, deleted = await purge_channel(channel, limit, status_hook=hook)
            cleaner_tab.toast(
                type="SUCCESS",
                title="Purge Complete",
                description=f"Deleted {deleted} messages after scanning {scanned}.",
            )
            update_status("Status: Ready")
        finally:
            ui_state["running"] = False
            button_ref.loading = False

    def determine_limit() -> Optional[int]:
        if delete_all_toggle.checked:
            return None
        raw = limit_input.value.strip()
        if not raw:
            return DEFAULT_LIMIT
        if not raw.isdigit():
            limit_input.invalid = True
            limit_input.error_message = f"Enter 1-{MAX_LIMIT}"
            return DEFAULT_LIMIT
        value = int(raw)
        if value < 1 or value > MAX_LIMIT:
            limit_input.invalid = True
            limit_input.error_message = f"Enter 1-{MAX_LIMIT}"
            return DEFAULT_LIMIT
        limit_input.invalid = False
        limit_input.error_message = None
        return value

    def update_status(message: str) -> None:
        status_text.content = message

    async def handle_channel_button():
        channel_id = channel_id_input.value.strip()
        if not channel_id.isdigit():
            channel_id_input.invalid = True
            channel_id_input.error_message = "Channel ID must be numeric"
            return

        save_settings({"channel_id": channel_id})

        async def resolver():
            return await safe_fetch_channel(int(channel_id))

        await run_ui_purge(resolver, determine_limit(), "server channel", channel_button)

    async def handle_group_button():
        group_id = group_id_input.value.strip()
        if not group_id.isdigit():
            group_id_input.invalid = True
            group_id_input.error_message = "Group ID must be numeric"
            return

        save_settings({"group_id": group_id})

        async def resolver():
            channel = await safe_fetch_channel(int(group_id))
            if isinstance(channel, discord.GroupChannel):
                return channel
            return None

        await run_ui_purge(resolver, determine_limit(), "group chat", group_button)

    async def handle_dm_button():
        dm_value = dm_input.value.strip()
        if not dm_value.isdigit():
            dm_input.invalid = True
            dm_input.error_message = "User or DM ID must be numeric"
            return

        save_settings({"dm_id": dm_value})

        async def resolver():
            channel = await safe_fetch_channel(int(dm_value))
            if isinstance(channel, discord.DMChannel):
                return channel
            return await resolve_dm_channel(int(dm_value))

        await run_ui_purge(resolver, determine_limit(), "direct message", dm_button)

    def on_limit_change(new_value: str):
        if not new_value:
            limit_input.invalid = False
            limit_input.error_message = None
            save_settings({"limit": new_value})
            return
        if not new_value.isdigit():
            limit_input.invalid = True
            limit_input.error_message = "Numbers only"
            return
        limit_input.invalid = False
        limit_input.error_message = None
        save_settings({"limit": new_value})

    def on_delete_all_change(checked: bool):
        limit_input.disabled = checked
        save_settings({"delete_all": checked})

    settings = load_settings()
    ui_state = {"running": False}

    cleaner_tab = Tab(name="Message Cleaner", title="Delete Messages", icon="trash")
    layout = cleaner_tab.create_container(type="columns")
    main_card = layout.create_card(gap=3)
    main_card.create_ui_element(UI.Text, content="Message Cleaner", size="xl", weight="bold")
    main_card.create_ui_element(
        UI.Text,
        content="Delete your own messages across servers, DMs, and groups. Respect Discord's ToS and only remove your content.",
        size="sm",
    )

    settings_group = main_card.create_group(type="columns", gap=3, full_width=True)
    limit_input = settings_group.create_ui_element(
        UI.Input,
        label="Amount to delete",
        placeholder=str(DEFAULT_LIMIT),
        value=settings.get("limit", str(DEFAULT_LIMIT)),
        onInput=on_limit_change,
        full_width=True,
    )
    delete_all_toggle = settings_group.create_ui_element(
        UI.Toggle,
        label="Delete ALL available messages",
        checked=settings.get("delete_all", False),
        onChange=on_delete_all_change,
    )
    limit_input.disabled = delete_all_toggle.checked

    channel_group = main_card.create_group(type="columns", gap=2, full_width=True)
    channel_id_input = channel_group.create_ui_element(
        UI.Input,
        label="Server channel / thread ID",
        placeholder="123456789012345678",
        value=settings.get("channel_id", ""),
        show_clear_button=True,
        full_width=True,
    )
    channel_button = channel_group.create_ui_element(
        UI.Button,
        label="Purge Server Channel",
        color="primary",
        full_width=False,
        onClick=handle_channel_button,
    )

    dm_group = main_card.create_group(type="columns", gap=2, full_width=True)
    dm_input = dm_group.create_ui_element(
        UI.Input,
        label="DM channel ID or user ID",
        placeholder="Enter ID",
        value=settings.get("dm_id", ""),
        show_clear_button=True,
        full_width=True,
    )
    dm_button = dm_group.create_ui_element(
        UI.Button,
        label="Purge Direct Message",
        color="primary",
        full_width=False,
        onClick=handle_dm_button,
    )

    group_section = main_card.create_group(type="columns", gap=2, full_width=True)
    group_id_input = group_section.create_ui_element(
        UI.Input,
        label="Group chat channel ID",
        placeholder="Enter group channel ID",
        value=settings.get("group_id", ""),
        show_clear_button=True,
        full_width=True,
    )
    group_button = group_section.create_ui_element(
        UI.Button,
        label="Purge Group Chat",
        color="primary",
        full_width=False,
        onClick=handle_group_button,
    )

    status_text = main_card.create_ui_element(UI.Text, content="Status: Ready", size="sm", color="var(--text-muted)")
    cleaner_tab.render()

    @bot.command(
        name="deletepersonalmessages",
        aliases=["dpm"],
        description="Delete your own messages in the current channel.",
        usage=f"{SCRIPT_ID} <amount|all>",
    )
    async def delete_personal_messages_command(ctx, *, argument: str = ""):
        await ctx.message.delete()
        limit = parse_amount_argument(argument)
        notify = await ctx.send("Message Cleaner: starting…", silent=True)

        async def hook(message: str):
            await notify.edit(content=f"Message Cleaner: {message}")

        _, deleted = await purge_channel(ctx.channel, limit, status_hook=hook)
        await notify.edit(content=f"Message Cleaner: deleted {deleted} messages.")

delete_personal_messages()
