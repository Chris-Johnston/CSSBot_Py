# CSSBot_Py
A bot for the CSS discord server, written in Python 3.6 using [discord.py](https://github.com/Rapptz/discord.py).

See also [CSSBot](https://github.com/Chris-Johnston/CSSBot), same idea just in C#.

# Installation / Setup / Usage

This project is meant for Python 3.6. Please ensure that you have that installed and working, then come back here.

## Prerequisites
You'll probably need to install a few packages first.

Linux:
```bash
python3.6 -m pip install -U git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py[voice]
sudo apt-get install libffi-dev python3.6-dev
```

## Setup

- Register your own discord bot for testing with.
  - Navigate to the Discord API docs and log in: https://discordapp.com/developers/applications/me (if you log in for the first time, it'll probably take you to the app, so go back again).
  - Click on the "New App" button
  - Name your app. Click "Create App"
  - Click "Crate a Bot User" (Discord API supports a few types of apps/bots, but we are building a bot)
  - Locate your bot's user token. **Your user token must not be shared with anyone. If it is posted publicly, change it ASAP.**
- Clone the repo using `git clone https://github.com/Chris-Johnston/CSSBot_Py.git`
- Create a new file in your CSSBot_Py directory: `config.ini`
  - Populate the file with the following contents:
  ```ini
  [Configuration]
  connection_token=XXXXXXXXXYOURTOKENGOESHEREXXXXXXX
  ```
  
## Usage

Run the following command:
```bash
python3.6 main.py
```

The first lines should read something like:
```
discordpy
1.0.0a
Logged in SomeUser - 1234567890
Version 1.0.0a
```

(for future consideration, considering looking into virtualenv, Docker, or just using a screen in the background to run the bot)

# Contributing

Feel free to add whatever changes in a pull request. Feature requests should be added under Issues.
All changes will be discussed before they are committed to the main branch.

## Reference Material

Here are some resources to get you started:

https://github.com/Rapptz/discord.py

https://discordapp.com/developers/docs/intro

http://discordpy.readthedocs.io/en/rewrite/

http://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html

https://gist.github.com/MysterialPy/d78c061a4798ae81be9825468fe146be
