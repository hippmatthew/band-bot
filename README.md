# Band Bot

Band Bot is a Discord bot that allows users to manage a song queue and play music in voice channels. The bot uses the `discord.py` library to interact with Discord and manage the song queue.

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/hippmatthew/band-bot.git
   cd band-bot
   ```

2. Create a virtual environment and activate it:
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory and add your Discord bot token:
   ```sh
   DISC_TOKEN=your_discord_bot_token
   ```

## Usage

1. Run the bot:
   ```sh
   python band_bot.py
   ```

2. Invite the bot to your Discord server using the OAuth2 URL provided by the Discord Developer Portal.

## Commands

- `/join`: Band Bot joins a voice channel.
- `/leave`: Band Bot leaves a voice channel.
- `/request <search>`: Band Bot accepts your music request and adds it to the queue.
- `/queue`: Band Bot displays the song queue.
- `/skip`: Band Bot skips the current song in the queue.
- `/artist <new_name>`: Band Bot invites a new artist to the bandstand (requires manage nicknames permission).
- `/clear`: Band Bot clears the song queue.
