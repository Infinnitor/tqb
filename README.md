# tqb

task queue board - a CLI utility for simple kanban-style project management

use `tqb help` to show the help menu, and `tqb help --examples` for example usage

# Install

## Linux

```bash
# ensure you have python3 and gcc installed
make install
# that's it, you're done!
# to remove:
make uninstall
```

## Windows

```powershell
# idk about a system install yet, but you can install the dependencies
python -m venv venv
venv/Scripts/Activate.ps1
pip install -r requirements.txt

# run
python src/main.py
```
