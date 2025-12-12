# Nighty Scripts

A small collection of scripts intended to be loaded into **Nighty**.

> Note: These scripts can perform irreversible actions (for example, deleting messages). Review the code and use at your own risk.

## Scripts

- [DeleteDms/](DeleteDms/) — "Message Cleaner" (deletes **your own** Discord messages from a server channel/thread, group chat, or DM). See [DeleteDms/README.md](DeleteDms/README.md).

## Getting started

1. Open the folder for the script you want (for example [DeleteDms/](DeleteDms/)).
2. Follow the instructions in that folder's README.
3. Import the `.py` file into Nighty and reload/restart scripts.

## Safety / expectations

- These scripts are intended to act only on the authenticated account (for example: deleting messages authored by you).
- Large operations may take time due to API rate limits.
- Ensure your usage complies with Discord's Terms of Service and any applicable local laws.

## Contributing

If you want a new script or improvement, open an issue/PR with:

- what Nighty feature/API you're using
- expected behavior
- minimal repro steps
