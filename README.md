# Silly Game

Took this exercise way too far and had a lot of fun with it.

## Dependencies
- Just `pynput` <- Warning this does legit take control of your keyboard so make sure to exit the game with "q" when you're done.

## Instalation
*Note:* Eventually, I may add some command-line flags so that you can say how big of a board you want and if you want to load a pre-existing board
- If using `pip`
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```
- if using `uv`
```bash
uv run main.py
```

## Gameplay
The keyboard controls are are based on vim keybindings, but I display them beneath the board so they're easy to remember.

Cascading crushes of letters (i.e. crushes that happen after their supporting letters have dropped) are rewarded more points than non-cascading crushes.

## Other Shit
- At some point, maybe I'll colorize the board and make it more animated
    - See letters drop, change their color in the case of matching, make it evident how many points you added, etc.
- A possibly fun extension of this would be to actually make a game server for this
    - This would be a big extension, and the game mechanics in their current state aren't fun enough to warrant it
    - Making it multiplayer with things like bombs, bricks, turn stealing, etc, could maybe make it worth it
    - Might also be cool to make it support multiple clients (TUI and Browser)
    - Would likely require persisting the game state
    - Another angle could be making the board arbitrarily large and having an infinite number of players

Anyways, this was fun.
