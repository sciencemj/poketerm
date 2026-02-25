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
uv tool run poketerm <flags>
or
poketerm <flags>
```
### Flags
- --dex: show pokedex info
- --id={num}: show pokemon of given id(different form is seprated by - ex)003, 003-2, 003-3)
- --size={num}: set the width of output(without this flag it will be auto)
