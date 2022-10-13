#!/usr/bin/env python

from __future__ import division, print_function

"""
This script generates a file to use for building authorea papers, and then runs
latex on them.

Requires python >= 2.6 (3.x should work, too)

The key assumptions are:
* ``layout.md`` exists in the article (I think it always does in Authorea)
* ``preamble.tex`` and/or``header.tex``, ``title.tex``, and
  ``bibliobgraphy/biblio.bib`` exist (I think these are created normally in a
    new Authorea article)
* ``posttitle.tex`` exists.  This one you'll have to create, containing
  everything you want after the title but before the beginning of the document.
  If it doesn't exist that's ok too, it'll just be ignored.
* Figures are in the ``figures`` directory (where authorea puts them), and in
  the correct place in the ``layout.md`` file.  A file named 'latexfigopts.json'
  can specify a dictionary for additional figure options (see the
  `FIGURE_DEFAULTS` below for what options that can be replaced).
  If pdf or eps figures exist alongside referenced raster image files, they will
  be favored over the raster format.

"""

import os
import sys
import shutil
import subprocess


#lots of dobule-{}'s are here because we use it as a formatting template below
MAIN_TEMPLATE = r"""
{preamblein}

{headerin}

% Bib if using BibLaTex, or set in preamble
% \addbibresource{{{bibloc}}}

\begin{{document}}

{titlecontent}

{sectioninputs}

% Use Bibtex or BibLaTex? (Set in preamble)
% \bibliography{{{bibloc}}}{{}}

\printbibliography

\end{{document}}
"""

FIGURE_TEMPLATE = r"""
\begin{<figure_env>}[<placement>]
\begin{center}
\includegraphics[width=<width>]{<figfn>}
<caption>
\end{center}
\end{<figure_env>}
""".replace('{', '{{').replace('}', '}}').replace('<', '{').replace('>', '}')

FIGURE_DEFAULTS = {'placement': '', 'width': '1\columnwidth', 'figure_env': 'figure'}


def get_input_string(filename, localdir, quotepath=True, flatten=False):
    if flatten:
        filepath = os.path.join(localdir, filename)
        if not os.path.exists(filepath):
            filepath = filepath + '.tex'

        with open(filepath, 'r') as f:
            return f.read()
    else:
        if filename.endswith('.tex'):
            filename = filename[:-4]
        if quotepath:
            quote_chr = '"'
        else:
            quote_chr = ''
        return r'\input{' + quote_chr + os.path.join(localdir, filename) + quote_chr + '}'


# Test HTML > LaTex, see notes below
# Parsing examples: https://stackoverflow.com/questions/328356/extracting-text-from-html-file-using-python
# Don't need much here - just want to remove HTML markup and grab label

from bs4 import BeautifulSoup

def get_input_string_HTML(filename, localdir, quotepath=True, flatten=False):
    """
    HTML captions > to tex.

    PH 05/09/22: basically working, but not general.
    Using BeautifulSoup for basic tag handling.
    Should also use Pandoc, but issues with inline maths...?
    """

    filepath = os.path.join(localdir, filename)
    if not os.path.exists(filepath):
        filepath = filepath + '.html'

    with open(filepath, 'r') as f:
#             return f.read()

        textIn = f.read()

    # textIn = textIn.replace('<b>',r'\textbf{').replace('</b>',r'}')   # Replace bold tags
    textIn = textIn.replace('<b>',r'\textbf{').replace('</b>',r'}').replace('%','\%')   #.replace('&','\&')   # Replace bold tags & % - should use Pandoc here!
                                                                                       # UGLY - & replace breaks &nbsp;

    soup = BeautifulSoup(textIn, 'html.parser')  # Parse HTML with BS

    clean_text = ' '.join(soup.stripped_strings) + f'\\label{{{soup.div["data-label"]}}}'
    clean_text = clean_text.replace('&','\&')


    # Return tex
    if flatten:
        return clean_text

    # Write .tex file
    else:
        if filename.endswith('.html'):
            filename = filename[:-5]

        with open(filepath[:-5] + '.tex', 'w') as f:
#             return f.read()

            f.write(clean_text)


        if quotepath:
            quote_chr = '"'
        else:
            quote_chr = ''
        return r'\input{' + quote_chr + os.path.join(localdir, filename) + quote_chr + '}'


def get_figure_string(filename, localdir, inputdir, flatten=False, copyto=False):
    import json
    import yaml

    # Read YML config file if exists and upadte figure file name...
    # configFile = os.path.join(inputdir, figdir, fignamebase, 'config.yml')
    # configFile = os.path.join(localdir, filename, 'config.yml')
    configFile = os.path.join(inputdir, filename, 'config.yml')

    if os.path.exists(configFile):
        with open(configFile, "r") as stream:
            try:
                configYML = yaml.safe_load(stream)
                filename = configYML['grid']['grid_elements'][0]['path']   # Update filename from YML
                # print(configYML)

                # Fig cases with alternative export filenames, e.g. HTML and PNG.
                if 'export-filename' in configYML.keys():
                    filename = os.path.join(os.path.split(filename)[0], configYML['export-filename'])   # Update filename from YML



            except yaml.YAMLError as exc:
                print(exc)


    figdir, figname = os.path.split(filename)

    fignamebase = os.path.splitext(figname)[0]
    figfn = os.path.join(inputdir, filename)

    pdffn = os.path.join(localdir, figdir, fignamebase + '.pdf')
    epsfn = os.path.join(localdir, figdir, fignamebase + '.eps')

    # PH 05/09/22 - couple of quick dir hacks
    # figSubDir = os.path.join(localdir, figdir, fignamebase)  # SET localdir here only?
    figSubDir = os.path.join(localdir, figdir)  # This case for YML version.

    if copyto:
        figpath = os.path.join(localdir, filename)
        if os.path.exists(pdffn):
            figpath = pdffn
            figfn = fignamebase
        elif os.path.exists(epsfn):
            figpath = epsfn
            figfn = fignamebase
        elif os.path.exists(figpath):
            figfn = figname
        else:
            raise IOError('Could not find figure file {}'.format(figpath))
        shutil.copy(figpath, os.path.join(copyto, os.path.split(figpath)[1]))

    else:
        # PH 06/09/22 - hack for html figs
        if figname.endswith('html'):
            # figname = figname[:-5]
            figfn = os.path.join(inputdir, figname[:-5])

        if os.path.exists(pdffn) or os.path.exists(epsfn):
            figfn = os.path.join(inputdir, figdir, fignamebase)

        # YET ANOTHER SINGLE CASE FIX - figs with original format `name.gv.pdf`  UGH.
        # print(figname)
        # print(figfn)
        if figname.endswith('.gv.png'):
            # figfn = os.path.join(inputdir, figname[:-7] + '-gv.pdf')
            figfn = os.path.join(inputdir, figname[:-4] + '.pdf')
            print(figfn)

        # PH 05/09/22 - couple of quick dir hacks
        if flatten:
            # figfn = filename   # Set for relative dir in flatten case?
            # figfn = os.path.join('figures', figname)  # Quick hack for flattened dir structure - UGLY.
            print(figfn)
            figfn = os.path.join('figures', os.path.split(figfn)[-1])
            print(figfn)

            # if os.path.exists(fignamebase, '.pdf'):
            #     figpath = pdffn
            #     figfn = fignamebase


    # PH 05/09/22 - modified for fig subdirs & added HTML option.

    if os.path.exists(os.path.join(figSubDir, 'caption.tex')):
        # capinput = get_input_string('caption', os.path.join(inputdir, figdir), False, flatten=flatten)
        capinput = get_input_string('caption', figSubDir, False, flatten=flatten)
        # caption = r'\caption{ \protect' + capinput.strip() + '}'
        caption = r'\caption{' + capinput.strip() + '}'

    elif os.path.exists(os.path.join(figSubDir, 'caption.html')):
#     print('HTML caption')

        capinput = get_input_string_HTML('caption', figSubDir, False, flatten=flatten)
        # caption = r'\caption{ \protect' + capinput.strip() + '}'
        caption = r'\caption{' + capinput.strip() + '}'

    else:
        caption = ''

    optsfn = os.path.join(localdir, figdir, 'latexfigopts.json')
    figopts = FIGURE_DEFAULTS.copy()
    if os.path.exists(optsfn):
        with open(optsfn) as f:
            optsjson = json.load(f)
        if not isinstance(optsjson, dict):
            raise ValueError('File "{0}" does not have a top-level dict'.format(optsfn))
        for k in FIGURE_DEFAULTS.keys():
            v = optsjson.pop(k, None)
            if v is not None:
                figopts[k] = v
        if len(optsjson) != 0:
            raise ValueError('Entries in "{0}" that were not understood: {1}'.format(optsfn, optsjson))

    figopts.update(locals())
    return FIGURE_TEMPLATE.format(**figopts)


# if builddir and local dir are the same set the paths used for input/include in
# the output tex file to be relative paths (this helps if sharing the created
# tex file with collaborator who don't use this script) otherwise use absolute
# paths. Alternatively, use the user defined option for whether relative or
# absolute paths are used.
def get_in_path(localdir, builddir, pathtype=None):
    """
    Figure out the path for a file in ``localdir`` relative to ``builddir``, or
    just use an absolute path dependeing on whether ``pathtype`` is 'rel' or
    'abs'. Or if it is None, pick relative only if ``localdir`` is the same as
    ``builddir``.
    """
    if pathtype == 'rel':
        return os.path.relpath(localdir, builddir)
    elif pathtype == 'abs':
        return os.path.abspath(localdir)
    elif pathtype is None:
        if builddir == localdir:
            return os.path.relpath(localdir, builddir)
        else:
            return os.path.abspath(localdir)
    else:
        raise ValueError('Invalid pathtype: "{0}"'.format(pathtype))


def build_authorea_latex(localdir, builddir, latex_exec, bibtex_exec, outname,
                         usetitle, dobibtex, npostbibcalls, openwith, titleinput,
                         dobuild, pathtype, flatten, copy_figs):
    if not os.path.exists(builddir):
        os.mkdir(builddir)

    if not os.path.isdir(builddir):
        raise IOError('Requested build directory {0} is a file, not a '
                      'directory'.format(builddir))

    # generate the main tex file as a string
    if os.path.exists(os.path.join(localdir, 'preamble.tex')):
        preamblein = get_input_string('preamble', get_in_path(localdir, builddir, pathtype), flatten=flatten)
    else:
        preamblein = ''
    if os.path.exists(os.path.join(localdir, 'header.tex')):
        headerin = get_input_string('header', get_in_path(localdir, builddir, pathtype), flatten=flatten)
    else:
        headerin = ''

    if not headerin and not preamblein:
        print("Neither preable nor header found!  Proceeding, but that's rather weird")


    if copy_figs:
        bibloc_abs = os.path.join(get_in_path(localdir, builddir, 'abs'), 'bibliography', 'biblio') + '.bib'
        shutil.copy(bibloc_abs, os.path.join(builddir, os.path.split(bibloc_abs)[1]))
        bibloc = 'biblio'
    else:
        bibloc = os.path.join(get_in_path(localdir, builddir, pathtype), 'bibliography', 'biblio')

        # PH 06/09/22 - force rel if flatten.
        if flatten:
            bibloc = os.path.join('bibliography', 'biblio')


    titlecontent = []
    if usetitle:
        if titleinput:
            titlestr = get_input_string('title', get_in_path(localdir, builddir, pathtype), flatten=flatten)
        else:
            with open(os.path.join(get_in_path(localdir, builddir, 'abs'), 'title.tex')) as f:
                titlestr = f.read()
        titlecontent.append(r'\title{' + titlestr + '}')

        # PH 06/09/22 - quick hack to add an authors.tex without moding layout.md
        if os.path.exists(os.path.join(localdir, 'authors.tex')):
            with open(os.path.join(get_in_path(localdir, builddir, 'abs'), 'authors.tex')) as f:
                authstr = f.read()
            titlecontent.append(authstr)


    sectioninputs = []
    with open(os.path.join(localdir, 'layout.md')) as f:
        for l in f:
            ls = l.strip()
            if ls == '':
                pass
            elif ls in ('posttitle.tex', 'title.tex', 'preamble.tex', 'header.tex'):
                pass # skip any that have been processed above
            elif ls in ('abstract.tex'):
                # add abstract to title content
                titlein = get_input_string('abstract', get_in_path(localdir, builddir, pathtype), flatten=flatten)
                titlecontent.append(r'\begin{abstract}' + titlein  + '\end{abstract}')
            elif ls.endswith('.html') or ls.endswith('.htm'):
                pass  # html files aren't latex-able
            elif ls.startswith('figures'):
                inpath = get_in_path(localdir, builddir, pathtype)
                sectioninputs.append(get_figure_string(ls, localdir, inpath, flatten=flatten,
                                                       copyto=builddir if copy_figs else False))
            else:
                sectioninputs.append(get_input_string(ls, get_in_path(localdir, builddir, pathtype), flatten=flatten))
    sectioninputs = '\n'.join(sectioninputs)

    if os.path.exists(os.path.join(localdir, 'posttitle.tex')):
        titlecontent.append(get_input_string('posttitle', get_in_path(localdir, builddir, pathtype), flatten=flatten))
        # swap this to before the abstract
        if r'\begin{abstract}' in titlecontent[-2]: # check second to last value and swap position
            titlecontent[-1], titlecontent[-2] = titlecontent[-2], titlecontent[-1]
    titlecontent = '\n'.join(titlecontent)

    maintexstr = MAIN_TEMPLATE.format(**locals())

    #now save that string out as a file
    outname = outname if outname.endswith('.tex') else (outname + '.tex')
    outtexpath = os.path.join(builddir, outname)
    with open(outtexpath, 'w') as f:
        f.write(maintexstr)

    if outname.endswith('.tex'):
        outname = outname[:-4]

    if dobuild:
        #now actually run latex/bibtex
        args = [latex_exec, outname + '.tex']
        print('\n\RUNNING THIS COMMAND: "{0}"\n'.format(' '.join([latex_exec, outname + '.tex'])))
        subprocess.check_call(args, cwd=builddir)
        if dobibtex:
            args = [bibtex_exec, outname]
            print('\n\RUNNING THIS COMMAND: "{0}"\n'.format(' '.join([latex_exec, outname + '.tex'])))
            subprocess.check_call(args, cwd=builddir)
        for _ in range(npostbibcalls):
            args = [latex_exec, outname + '.tex']
            print('\n\RUNNING THIS COMMAND: "{0}"\n'.format(' '.join([latex_exec, outname + '.tex'])))
            subprocess.check_call(args, cwd=builddir)

        #launch the result if necessary
        resultfn = outtexpath[:-4] + ('.pdf' if 'pdf' in latex_exec else '.dvi')
        if openwith:
            args = openwith.split(' ')
            args.append(resultfn)
            print('\nLaunching as:' + str(args), '\n')
            subprocess.check_call(args)
        else:
            msg = '\nBuild completed.  You can see the result in "{0}": "{1}"'
            print(msg.format(builddir, resultfn), '\n')
    else:
        msg = 'Preprocessing done but skipping build.  Main file:"{0}.tex"'
        print(msg.format(os.path.join(builddir, outname)))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Local builder for authorea papers.')

    parser.add_argument('localdir', nargs='?', default='.',
                        help='The directory to actually search for the authorea'
                             ' files in. Default to the current directory.')
    parser.add_argument('--build-dir', '-d', default='authorea_build',
                        help='the directory to build the paper in')
    parser.add_argument('--latex', '-l', default='pdflatex',
                        help='The executable to use for the latex build step.')
    parser.add_argument('--bibtex', '-b', default='bibtex',
                        help='The executable to use for the bibtex build step.')
    parser.add_argument('--filename', '-f', default='authorea_paper',
                        help='The name to use for the output tex file.')
    parser.add_argument('--no-bibtex', action='store_false', dest='usebibtex',
                        help='Provide this to not run bibtex.')
    parser.add_argument('--no-title', action='store_false', dest='usetitle',
                        help='Provide this to skip the title command.')
    parser.add_argument('--title-input', action='store_true', dest='titleinput',
                        help='Provide this to have the title included via the '
                             '\\input command instead of directly in the '
                             'generated tex file. This is useful because \\input'
                             'sometimes prevents the title from being cased '
                             'correctly.', default=False)
    parser.add_argument('--n-runs-after-bibtex', '-n', type=int, default=3,
                        help='The number of times to call latex after bibtex.')
    parser.add_argument('--open-with', '-o', default=None,
                        help='An executable to launch the output file with. '
                             'Default is to not do anything with it.')
    parser.add_argument('--no-build', action='store_false', dest='dobuild',
                        help='Only do preprocessing and skip all the build/open steps')
    parser.add_argument('--relative-links', action='store_true', dest='rellinks',
                        help='Always make links (to input files and figures) within '
                             'the .tex file relative. Default is to do this if '
                             'localdir and buildir are the same.')
    parser.add_argument('--absolute-links', action='store_true', dest='abslinks',
                        help='Always make links (to input files and figures) within '
                             'the .tex file absolute. Default is to do this if '
                             'localdir and buildir are different.')
    parser.add_argument('--flatten', '-t', action='store_true',
                        help=r'Directly includes the content from tex files '
                             r'instead of using \input.')
    parser.add_argument('--copy-figs', '-c', action='store_true',
                        help='Copy figures and any bib files into the build '
                             'directory and set includes to point to those copies.')

    args = parser.parse_args()

    pathtype = None

    if args.flatten and (args.rellinks or args.abslinks):
        print('You cannot use both "--flatten" and either "--relative-links" '
              'or "--absolute-links".')
        sys.exit(1)

    if args.rellinks and args.abslinks:
        print('You must use either "--relative-links", "--absolute-links", or '
              'neither, but not both.')
        sys.exit(1)
    else:
        if args.rellinks:
            pathtype = 'rel'
        if args.abslinks:
            pathtype = 'abs'

    build_authorea_latex(args.localdir, args.build_dir, args.latex, args.bibtex,
                         args.filename, args.usetitle, args.usebibtex,
                         args.n_runs_after_bibtex, args.open_with,
                         args.titleinput, args.dobuild, pathtype, args.flatten,
                         args.copy_figs)
