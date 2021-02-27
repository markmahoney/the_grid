# The Grid wishlist exporter for DIM
An exporter and hosting location for tooling that turn's amhorton's [spreadsheet of desirable and grindable Destiny 2 loot](https://docs.google.com/spreadsheets/d/1fPE6BTWjTZlfNOGp6kPOrT6ZqUMasbgHQzJanyHnz48/edit?usp=sharing) into a usable wishlist for Destiny Item Manager.

## How to Use
In DIM, go to `Settings -> Wish List -> Optionally, supply the URL(s) for a wish list (pipe | separated)`, and then paste this in there:

```
https://raw.githubusercontent.com/markmahoney/the_grid/main/the_grid.tsv
```

If you'd like to keep the default DIM wishlist in addition to using The Grid, paste this big ol' thing in there instead:

```
https://raw.githubusercontent.com/48klocs/dim-wish-list-sources/master/voltron.txt | https://raw.githubusercontent.com/markmahoney/the_grid/main/the_grid.tsv
```

Note: the original version of this file was located at `https://raw.githubusercontent.com/markmahoney/the_grid/main/DESTINY_2_-_THE_GRID_season_13_-_dim.tsv`, but that file is going to be deleted soon. Please use one of the two options listed above instead.

TODO: add git tags for each season (and maybe seasonal revisions?), so people can wishlist specific versions of The Grid if they want to.

## Updating the Wishlist TSV
You need to have Python 3 installed on your system. Then you should just be able to type

```sh
make
```

and it'll eventually crap out an updated version of `the_grid.tsv`.

TODO: add tooling to automate tagging and pushing updates.

## Credits
- amhorton: creator and maintainer of The Grid
- shoes: wrote the Python generator for exporting The Grid to a DIM wishlist TSV
- PoofPactory: was in voice chat while shoes was writing the generator
- Windows98: said "youre all welcome" in the Ghost Proxy Discord, so he must've done something
