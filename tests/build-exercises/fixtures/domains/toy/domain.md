# Toy

Applies to: a Curriculum whose subject is the Toy engine, a stand-in domain for the `exercises.py` tests.

## Environment

### Tool

`toy` must be on PATH. `toy --version` prints the version; it matches a Target version when the Target version is a dotted prefix of the output.

### Self-contained

One Toy project per Exercise.

### Project layout

Given code and learner code are `.toy` files at the project root. The marker is `# Your code goes here.`

### Building the starter

None.

## Checking

### Harness

`check/harness.txt` runs the check lines and prints the summary.

### Check lines

The author writes them in `check/lines.txt`, one `expect` per line.

### Stand-ins

None.
