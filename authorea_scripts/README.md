# authorea-scripts

Scripts for working with Authorea articles.

Original version: https://github.com/eteq/authorea-scripts - with thanks to eteq!

**This version: hack modifications for generating flat Tex for Overleaf builds, with Authorea mods 2022**
(PH 08/09/22)

Script to compile single .tex document from Authorea's `layout.md` file and parts, and (optionally) build to PDF and wrangle figures.

Two slightly different flavours [`local_build_HTMLcaption.py`](https://github.com/phockett/Extracting-Molecular-Frame-Photoionization-Dynamics-from-Experimental-Data/blob/submission050922/authorea_scripts/local_build_HTMLcaptions.py) and [`local_build_HTMLcaptions_Overleafconfig.py`](https://github.com/phockett/Extracting-Molecular-Frame-Photoionization-Dynamics-from-Experimental-Data/blob/submission050922/authorea_scripts/local_build_HTMLcaptions_Overleafconfig.py), the latter should be best.


## Main changes for Authorea in 2022 & use with Overleaf

- Deal with HTML files for figure captions (basic implementation with tag-stripping via BeautifulSoup only), see function [`get_input_string_HTML()`](https://github.com/phockett/Extracting-Molecular-Frame-Photoionization-Dynamics-from-Experimental-Data/blob/af2149b6e9cc75d1f2bd970e5893c9840a25626f/authorea_scripts/local_build_HTMLcaptions_Overleafconfig.py#L121).
- Added [read figure config.yml files to `get_figure_string()`](https://github.com/phockett/Extracting-Molecular-Frame-Photoionization-Dynamics-from-Experimental-Data/blob/af2149b6e9cc75d1f2bd970e5893c9840a25626f/authorea_scripts/local_build_HTMLcaptions_Overleafconfig.py#L192) to determine correct figure from fig subdirs when multiple versions present.
- Build for flat figure file structure, `build_dir/figures` (note this is [hard-coded in some places](https://github.com/phockett/Extracting-Molecular-Frame-Photoionization-Dynamics-from-Experimental-Data/blob/af2149b6e9cc75d1f2bd970e5893c9840a25626f/authorea_scripts/local_build_HTMLcaptions_Overleafconfig.py#L405), sorry).
- Some custom LaTex template mods (hard-coded), [see top of scripts for templates](https://github.com/phockett/Extracting-Molecular-Frame-Photoionization-Dynamics-from-Experimental-Data/blob/af2149b6e9cc75d1f2bd970e5893c9840a25626f/authorea_scripts/local_build_HTMLcaptions_Overleafconfig.py#L56).

E.g. build master file `overleaf_master.tex` for Overleaf (from script dir):

```
python local_build_HTMLcaptions_Overleafconfig.py ../ -f overleaf_master.tex --build-dir ../builds --flatten --no-build

```


## Notes

- Building complete source .tex file with `--flatten` works properly. Some other functionality might be broken due to hacky path wrangling.
- Building with `--copy-figs` copies figures to build_dir/figures OK, but paths in Tex file may be inconsistent.
- initial build may require manually-created `preamble.tex` and `authors.tex`.
