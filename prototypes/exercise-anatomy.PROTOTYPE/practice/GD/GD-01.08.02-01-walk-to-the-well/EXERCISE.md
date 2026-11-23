# Walk to the well

- Curriculum: GD
- Anchor: GD-01.08.02
- Anchor title: Moving a CharacterBody3D
- Target version: 4.7.2

## Task

Open this folder as a project in Godot and run `main.tscn`. A villager hangs in the air above a field. Beyond the field a gentle ramp climbs to a plateau, and at the far side a steep stone slope leads up to a well the villager can't reach.

Make the villager walk to the well. Write your code in `villager.gd`, below `# Your code goes here.` `heading()` and `speed` are given: `heading()` returns the flat direction toward the well, and `speed` is how fast the villager walks.

## Done when

- The villager falls to the ground and stays on it.
- It walks toward the well at `speed`, 3 meters per second, whatever the frame rate.
- It walks up the 30-degree ramp onto the plateau.
- It can't climb the 60-degree slope. It stops at its foot, still pressing toward the well, and reports touching both a wall and the floor.
- It moves only on physics ticks.

Change only `villager.gd`. The level, the villager's scene and `heading()` stay as given.

## Check

Run `./check.sh` from this folder. Each line says what it tested; it exits 0 when everything passes.

## Stuck?

`hints/` holds three hints, each more direct than the last. Open `hints/1.md` first, and the next only if you're still stuck.
