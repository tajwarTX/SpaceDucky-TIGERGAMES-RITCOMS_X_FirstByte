#!/usr/bin/env bash
# Run this once from inside the space-ducky folder.
# It copies your game file (play.py) from the Desktop into the repo and makes the first commit.
set -e
if [ ! -f play.py ]; then
  if [ -f "$HOME/Desktop/play.py" ]; then
    cp "$HOME/Desktop/play.py" ./play.py
    echo "Copied play.py from Desktop."
  else
    echo "Put your play.py in this folder first." && exit 1
  fi
fi
# Make the game load sprites from the repo's assets/ folder first
python3 - << 'PY'
src = open("play.py").read()
old = "POSSIBLE_PATHS = [\n"
new = "POSSIBLE_PATHS = [\n    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets'),\n"
if "'assets'" not in src and old in src:
    open("play.py", "w").write(src.replace(old, new, 1))
    print("Patched play.py to load sprites from assets/.")
PY

git init -b main
git add .
git commit -m "Space Ducky: Tiger Games '26 Best Solo Game"
echo
echo "Done. Now create an empty repo named space-ducky on github.com, then run:"
echo "  git remote add origin https://github.com/<your-username>/space-ducky.git"
echo "  git push -u origin main"
