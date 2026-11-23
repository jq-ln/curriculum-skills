# Save the colony

- Curriculum: GD
- Anchor: GD-06.03.01
- Anchor title: A save system with groups and dictionaries
- Target version: 4.7.2

## Task

Open this folder as a project in Godot and run `main.tscn`. A small colony appears: villagers (capsules) and fields (flat boxes) under `World`, plus a few rocks for decoration. While it runs, F2 scrambles the colony: villagers move, get hungrier and drop wheat, fields reset, one villager leaves and a newcomer arrives. F5 calls `save_game()` and F9 calls `load_game()`, and both are empty.

Make F5 save the colony to `user://savegame.save` and F9 bring back exactly the colony that was saved, using the save pattern from the manual. Write your code in `main.gd`, `villager.gd` and `field.gd`, where they say `# Your code goes here.`

## Done when

- `save_game()` writes one JSON line per villager and per field, and each line names the scene file the node was instanced from and its parent.
- After a scramble, `load_game()` brings back the saved villagers and fields, no more and no fewer, each under its own parent node, with its position and all its other values as saved.
- Inventory counts come back as whole numbers (`int`), as they were saved.
- Loading twice in a row gives the same colony as loading once.
- The rocks aren't saved, and loading leaves them alone.

`populate()`, `scramble()`, the key handling and the scenes stay as given. How each node describes itself and how it's rebuilt is up to you.

## Check

Run `./check.sh` from this folder. It deletes any old save, saves, scrambles, loads, compares, and loads again. Each line says what it tested; it exits 0 when everything passes.

## Stuck?

`hints/` holds three hints, each more direct than the last. Open `hints/1.md` first, and the next only if you're still stuck.
