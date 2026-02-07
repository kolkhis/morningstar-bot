# Morningstar Discord Bot

This is a custom Discord bot for the Morningstar server.  

Its primary purpose is to facilitate the events run in the server (mainly
giveaway events).  


## Ideas

- Questions will be read from a json file, with a `asked` key set to the value
  of the date it was asked, and `null` if it has not been asked. Only questions
  that have not been asked already will be posted (unless no unasked questions
  remain).  
    - Possible question format:
      ```json
      {
        "version": 1,
        "next_index": 0,
        "questions": [
          {
            "id": "q_000001",
            "text": "What did you learn today?",
            "added_by": 123456789012345678,
            "added_at": "2026-02-03T15:55:00-05:00",
            "active": true,
            "used_count": 0,
            "last_used": null,
            "tags": []
          }
        ]
      }
      ```

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



## Resources

- [`discord.ext.tasks` Documentation](https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html)

