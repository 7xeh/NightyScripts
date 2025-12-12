# Nighty Message Cleaner

[← Back to Nighty Scripts](../README.md)

The **Message Cleaner** script adds both a Nighty UI tab and a legacy `dpm` command that delete **your own** Discord messages across servers, group chats, and direct messages.

## Features

- UI tab with inputs for channel, DM/user, and group IDs
- Optional delete-all toggle plus a numeric limit (default 100)
- Works in servers, threads, group chats, and DMs (self messages only)
- Slash-style command fallback: `dpm <amount|all>` inside any channel
- Status feedback with real-time progress updates

## Usage

1. Import the script into Nighty and restart/reload scripts.
2. Open Nighty, go to the **Message Cleaner** tab.
3. Provide the target ID: server channel/thread ID, user/group ID, or DM channel ID.
4. Pick how many recent self messages to delete (or toggle **Delete ALL**).
5. Press the appropriate purge button.

### Command shortcut

Type `dpm 50` (or `dpm all`) inside any channel/DM/group to purge your own messages from the current conversation.

## Notes

- Nighty can only delete messages sent by your account.
- Respect Discord’s Terms of Service and local regulations.
- Massive deletions may take time because of API rate limits.
