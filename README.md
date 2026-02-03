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

Once the virtual environment is created, set the following lines in the
`venv/bin/activate` venv activation script.  
```bash
export BOT_TOKEN="$(head -1 ~/.config/discord/MORNINGSTAR_TOKEN)"
export GUILD_ID="1234567890"
```
This will safely pull the bot token from a file of your choosing. In this case,
it is the `MORNINGSTAR_TOKEN` file in my `~/.config/discord` directory. You
will need to create this directory yourself.  

The file should contain only one line, the bot token itself. Ensure the file 
has the proper read permissions for the user account that is running it.  

The `GUILD_ID` can either be hardcoded in the `activate` script, or can be
pulled from a file in the same fashion as the `BOT_TOKEN` variable. This is
the Discord server ID, obtained by right clicking on the server name at the top
left and selecting "Copy server ID" (requires developer mode to be enabled).  
This variable is used to more quickly sync slash commands with the server.  




