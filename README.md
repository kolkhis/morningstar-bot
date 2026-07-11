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
- [x] Refactor the `created_at` row entries in the giveaways table to use a non-
  deprecated function for getting current time.  
    - Currently using `dt.datetime.utcnow().isoformat()` which is deprecated.  

- [x] Add level check functionality to determine event eligibility
- [x] Add a command to output all members of a given level
- [ ] Add ticket system for people to request coaching

### Tremendous API Integration (Coffee Fund)

Starting commands:

- `/coffee setup`
    - Opens a modal that stores name and email
- `/coffee claim email name`
    - check if user has profile
    - check that user hasn't claimed this month
    - insert pending claim into db table (`coffee_claims`)
    - call tremendous API
    - update claim with order/reward IDs and status
    - reply 
- `/coffee status`

Eventual Commands:

- `/coffee claim`
- `/coffee status`
- `/coffee setup-email`
- `/coffee admin-balance`
- `/coffee admin-reset-user`
- `/coffee admin-disable`

#### Environment Vars

```bash
export TREMENDOUS_API_KEY='...'
export TREMENDOUS_BASE_URL='https://testflight.tremendous.com/api/v2'
export TREMENDOUS_PRODUCT_ID='...'
export COFFEE_AMOUNT_USD='5'

# for prod:
export TREMENDOUS_BASE_URL='https://api.tremendous.com/api/v2'
```

#### DB Schema

add user payout profiles
```SQL
CREATE TABLE IF NOT EXISTS coffee_profiles (
    user_id INTEGER PRIMARY KEY,
    recipient_name TEXT NOT NULL,
    recipient_email TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

add a claim ledger
```SQL
CREATE TABLE IF NOT EXISTS coffee_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    claim_month TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    currency_code TEXT NOT NULL,
    tremendous_order_id TEXT,
    tremendous_reward_id TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(user_id, claim_month)
);
```

- `UNIQUE(user_id, claim_month)` will prevent someone from claiming twice in
  the same month. Format like `2026-07`


#### Tremendous order payload
Formatted as follows
```json
{
  "payment": {
    "funding_source_id": "BALANCE"
  },
  "reward": {
    "value": {
      "denomination": 50,
      "currency_code": "USD"
    },
    "delivery": {
      "method": "EMAIL"
    },
    "recipient": {
      "name": "Jane Doe",
      "email": "person@example.com"
    },
    "products": [
      "OKMHM2X2OHYV"
    ]
  }
}
```

#### Abuse prevention

- one claim per Discord user per calendar month
- require a specific eligible role
- log every claim to an admin channel
- store Tremendous order ID and reward ID
- use sandbox first
- no public reward links (email only)
- prod command disabled by default until configured

---

- monthly total budget cap
- per-user amount cap
- admin enable/disable switch
- manual approval mode for first version
- account age / server join age check??







