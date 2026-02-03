# Morningstar Discord Bot

This is a custom Discord bot for the Morningstar server.  

Its primary purpose is to facilitate the events run in the server (mainly
giveaway events).  



## Ideas

- Questions will be read from file, removed once posted and then put into a
  different `finished.txt` (or something).  
    - When the prompt file is empty, do not post? Or post a random question
      from `finished.txt`?  

- Commands (admin):
    - /addquestion "text"
    - /listquestions (show like 20~?)
    - /setposttime (change the schedule)
    - /removequestion number:42 (maybe?)
    - /previewnext to show what will be posted tomorrow

- Add tags automatically ("Daily", "Question")

## Local Setup
To run this bot locally, set up a Python virtual environment.  
```bash
python3 -m venv venv
```
**Note:** This requires the `python3.10-venv` package on Debian-based systems.

Once the virtual environment is created, set the following line in the
`venv/bin/activate` venv activation script.  
```bash
export BOT_TOKEN="$(head -1 ~/.config/discord/MORNINGSTAR_TOKEN)"
```
This will safely pull the bot token from a file of your choosing. In this case,
it is the `MORNINGSTAR_TOKEN` file in my `~/.config/discord` directory. You
will need to create this directory yourself.  

The file should contain only one line, the bot token itself.  



```html
https://discord.com/oauth2/authorize?client_id=1465862547088347179&permissions=8&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A80&integration_type=0&scope=identify+guilds+guilds.channels.read+guilds.join+presences.write+applications.commands+messages.read+activities.invites.write+presences.read+webhook.incoming+rpc+applications.builds.read+applications.entitlements+voice+dm_channels.messages.read+activities.read+openid+sdk.social_layer+bot+connections+guilds.members.read+applications.builds.upload+applications.store.update+activities.write+relationships.write+role_connections.write+gateway.connect+sdk.social_layer_presence+application_identities.write+email+gdm.join
```
