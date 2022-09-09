# authorea-scripts

Scripts for working with Authorea articles.

Original version: https://github.com/eteq/authorea-scripts
With thanks to eteq!


**This version: hack modifications for generating flat Tex for Overleaf builds, with Authorea mods 2022**
PH 08/09/22

Two slightly different flavours `local_build_HTMLcaption.py` and `local_build_HTMLcaptions_Overleafconfig.py`, the latter should be best.


## Main changes for Authorea in 2022 & use with Overleaf

- Deal with HTML files for figure captions (basic implementation only), see function get_input_string_HTML().
- Read figure config.yml files to determine correct figure from fig subdirs.
- Build for flat figure file structure, 'build/figures'.
- Some custom template mods.


## Notes

- building with `--flatten` works properly. Some other functionality might be broken due to hacky path wrangling.
- building with `--copy-figs` copies figures to build_dir/figures OK, but paths in Tex file may be inconsistent.
- initial build may require manually-created preamble.tex and authors.tex.
