# Morningstar Discord Bot

This is a custom Discord bot for the Morningstar server.  

Its primary purpose is to facilitate the events run in the server (mainly
giveaway events).  

## New Bot

This bot will have:

- a leveling system based on message count
- a weekly giveaway post that gets created automatically
- an entry validation system that only accepts users who:
    - reacted with the right emoji
    - are level 10
    - have the @Giveaway and @Morningstar roles
- a winner picker that chooses:
    - one random reward from 3 possible rewards
    - one random valid winner

Build with:

- `on_message()` event listener to track message count and assign levels
    - One level per 50 messages, up to level 10
- `tasks.loop()` to create weekly giveaway posts
- `on_reaction_add()` event listener to validate entries and pick winners
- `random.choice()` to select random rewards and winners (after validating entries)
- Possible SQLite table for users and their message counts/levels 

## Environment Variables
- `DISCORD_BOT_TOKEN`: The token for the Discord bot (required)
- `GIVEAWAY_CHANNEL_ID`: The ID of the channel where giveaway posts will be
- `GUILD_ID`: The ID of the Discord server (guild) where the bot operates

## Data Model
### User Data
Basic SQLite table for users and their message counts/levels:
```sql
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    message_count INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 0
);
```
This stores each user's ID, their total message count, and their current level.

The bot will update this table whenever a user sends a message, and it will
check the user's level when they react to the giveaway post.

### Giveaway Data
We can also create a table to store giveaway entries:
```sql
CREATE TABLE IF NOT EXISTS giveaways (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    reward TEXT NOT NULL,
    emoji TEXT NOT NULL,
    created_at TEXT NOT NULL,
    ended INTEGER NOT NULL DEFAULT 0
);
```
This table stores info about each giveaways. Includes guild ID (server ID),
channel ID, and message ID to link it to the giveaway post.  
Stores the emoji used for entry validation, the reward that was chosen for the
giveaway, and a flag to check if giveaway has ended (0 for active, 1 for ended).

### Winner Data
```sql
CREATE TABLE IF NOT EXISTS winners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    giveaway_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    reward TEXT NOT NULL,
    selected_at TEXT NOT NULL
);
```
This table stores the winners of each giveaway, linking them to the giveaway 
and the reward they won.


## Possible Bot Structure
```txt
bot/
├── main.py
├── db.py
├── leveling.py
├── giveaway.py
└── config.py
```


## TODO
Refactor the `created_at` row entries in the giveaways table to use a
non-deprecated function for getting current time.  
Currently using `dt.datetime.utcnow().isoformat()` which is deprecated.  


