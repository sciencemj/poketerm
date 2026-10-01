# Poketerm
![Example Image](./example.png)

**Python CLI Pokemon tool!**
Watch random pokemon image in terminal!
## Install
```bash
git clone https://github.com/sciencemj/poketerm.git
cd poketerm
uv tool install . --force
```
## Usage
```bash
poketerm <flags>
or (inside the cloned repo, without installing)
uv run poketerm <flags>
```
### Flags
- --dex: show pokedex info
- --id={num|name}: show pokemon of given id or name (different form is separated by - ex)003, 003-2, 003-3, mr-mime)
- --size={num}: set the width of output(without this flag it will be auto)
