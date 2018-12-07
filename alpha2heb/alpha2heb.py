#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
#    alpha2heb Copyright (C) 2018 Suizokukan
#    Contact: suizokukan _A.T._ orange dot fr
#
#    This file is part of alpha2heb.
#    alpha2heb is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    alpha2heb is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with alpha2heb.  If not, see <http://www.gnu.org/licenses/>.
################################################################################
"""
        alpha2heb by suizokukan (suizokukan AT orange DOT fr)

        A (Python3/GPLv3/Linux/CLI) project, using no additional
        modules than the ones installed with Python3.

        alphabetic text → translitteration → Hebrew text

        see README.md for more documentation.
        ________________________________________________________________________

        alphaheb.py : entry point in the project.
"""
import re
import sys

import globals

from logger import LOGGER
import cfgini

import fb1d_fb4f

from utils import stranalyse, match_repr, extracts, extract_around_index
from cmdline import read_command_line_arguments

def add_firstlast_marker(src):
    LOGGER.pipelinetrace("add_firstlast_marker",
                         "add markers for the first and last characters")
    return "$"+src+"$"

def remove_firstlast_marker(src):
    LOGGER.pipelinetrace("remove_firstlast_marker",
                         "remove markers for the first and last characters")
    return src[1:-1]

def replace_and_log(pipeline_part, comment, src, before, after):
    """
        simply return src.replace(before, after) but with a log message
    """
    if before in src:
        LOGGER.pipelinetrace(pipeline_part,
                             "%s : '%s' > '%s' in %s",
                             comment, before, after, extracts(before, src))
        return src.replace(before, after)

    LOGGER.debug("[D01] Nothing to do in '%s' for %s : '%s' > '%s' in \"%s\"",
                 src, comment, before, after, extracts(before, src))
    return src

def sub_and_log(cfgini_flag, pipeline_part, comment, before, after, src):
    """
        simply return re.sub(before, after, src) with a log message if cfgini_flag.lower() == "true"
    """
    if cfgini_flag.lower() != "true":
        LOGGER.debug("[D02] Nothing to do in '%s' for %s : '%s' > '%s' in %s",
                     src, comment, before, after, extracts(before, src))

    if before in src:
        LOGGER.pipelinetrace(pipeline_part,
                             "%s : '%s' > '%s' in '%s'",
                             comment, before, after, extracts(before, src))
        return re.sub(before, after, src)

    LOGGER.debug("[D03] Nothing to do in '%s' for %s : '%s' > '%s' in %s",
                 src, comment, before, after, extracts(before, src))

    return src

def read_symbols(filename):
    LOGGER.debug("[D04] read_symbols : '%s'", filename)

    success = True
    errors = []

    alpha2hebrew = dict()
    with open(filename) as symbols:
        for line_index, _line in enumerate(symbols.readlines()):
            line = _line.strip()

            if '#' in line:
                line = line[:line.index('#')]
                line = line.strip()

            if line != "":
                if '→' in line:
                    alpha, hebrew = line.split("→")
                    alpha = alpha.strip()
                    hebrew = hebrew.strip()
                    if alpha in alpha2hebrew:
                        errors.append("key '{0}' has alread been defined; "
                                      "new definition in line {1} (line #{2})".format(alpha,
                                                                                      line,
                                                                                      line_index))
                        success = False
                    alpha2hebrew[alpha] = hebrew

    keys = sorted(alpha2hebrew.keys(), key=len, reverse=True)

    if not keys:
        success = False
        errors.append("empty alpha2hebrew dict")

    return success, errors, alpha2hebrew, keys

def transf__text_alpha2hebrew(_src):
    src = _src.group("rtltext")

    for alphachar in ALPHA2HEBREW_KEYS:
        src = replace_and_log("transf__text_alpha2hebrew",
                              "[transf__text_alpha2hebrew]",
                              src, alphachar, ALPHA2HEBREW[alphachar])

    LOGGER.pipelinetrace("transf__text_alpha2hebrew",
                         "Adding globals.RTL_SYMBOLS to '%s' : '%s' and '%s'",
                         src, globals.RTL_SYMBOLS[0], globals.RTL_SYMBOLS[1])

    return globals.RTL_SYMBOLS[0]+src+globals.RTL_SYMBOLS[1]

def transf__improve_rtlalphatext(src):
    src = sub_and_log(cfgini.CFGINI["pipeline.improve rtlalphatext"]["final kaf"],
                      "transf__improve_rtlalphatext",
                      "final kaf",
                      "ḵ:(?P<ponctuation>)", "ḵ²:\\g<ponctuation>", src)

    src = sub_and_log(cfgini.CFGINI["pipeline.improve rtlalphatext"]["alef + holam > alef + point_on_right"],
                      "transf__improve_rtlalphatext",
                      "alef + holam > alef + point_on_right",
                      "Aô", "A°", src)

    src = sub_and_log(cfgini.CFGINI["pipeline.improve rtlalphatext"]["ḥe + holam + shin > ḥe + shin"],
                      "transf__improve_rtlalphatext",
                      "ḥe + holam + shin > ḥe + shin",
                      "ḥ(?P<accent>[<])?ôš", "ḥ\\g<accent>š", src)

    return src

def transf__invert_rtltext(src):
    res = src.group("rtltext")[::-1]
    res = globals.RTL_SYMBOLS[0]+res+globals.RTL_SYMBOLS[1]

    LOGGER.pipelinetrace("transf__invert_rtltext",
                         "inverting the text : '%s' > '%s'",
                         match_repr(src), res)

    return res

def transf__use_FB1D_FB4F_chars(_src):
    src = _src.group("rtltext")

    # ---- 1/2 FB1D-FB4F characters : ----
    for shortname, (fullname, before, after) in fb1d_fb4f.TRANSF_FB1D_FB4F:

        if cfgini.CFGINI["pipeline.use FB1D-FB4F chars"][fullname].lower() == "true":
            pipeline_part = "transf__use_FB1D_FB4F_chars"
            comment = "{0}::{1}".format("transf__use_FB1D_FB4F_chars",
                                        fullname)
            src = replace_and_log(pipeline_part, comment, src, before, after)

    # ---- 2/2 let's add the first/last chars removed by calling this function ----
    LOGGER.pipelinetrace("transf__use_FB1D_FB4F_chars",
                         "Adding globals.RTL_SYMBOLS to '%s' : '%s' and '%s'",
                         src, globals.RTL_SYMBOLS[0], globals.RTL_SYMBOLS[1])

    return globals.RTL_SYMBOLS[0]+src+globals.RTL_SYMBOLS[1]

def output_html(inputdata):
    LOGGER.debug("[D05] [output_html] : data to be read=%s", inputdata)

    rtl_start = '<span class="rtltext" dir="rtl">'
    rtl_end = '</span>'

    header = []
    header.append("<!DOCTYPE html>")
    header.append("")
    header.append("<html>")
    header.append("")
    header.append("<head>")
    header.append("    <title>Page Title</title>")
    header.append('    <meta http-equiv="content-type" content="text/html; charset=utf-8" />')
    header.append("    <style>")
    header.append("        body {")
    header.append('          {0}'.format(cfgini.CFGINI["output.html"]["body"]))
    header.append("          }")
    header.append("")
    header.append("        .rtltext {")
    header.append('          {0}'.format(cfgini.CFGINI["output.html"]["rtltext"]))
    header.append("        }")
    header.append("    </style>")
    header.append("</head>")
    header.append("")
    header.append("<body>")
    header.append("")
    header = "\n".join(header)

    # transformation html.1::text_delimiters
    #    let's add a char at the very beginning and at the very end of the
    #    source string.
    inputdata = add_firstlast_marker(inputdata)

    # transformation html.2::maingroup
    inputdata = transf__maingroup(inputdata)

    # transformation html.3::br
    inputdata = inputdata.replace("\n", "<br/>\n")

    # transformation html.4::RTL_SYMBOLS
    inputdata = inputdata.replace(globals.RTL_SYMBOLS[0], rtl_start)
    inputdata = inputdata.replace(globals.RTL_SYMBOLS[1], rtl_end)

    # transformation html.5::undo_text_delimiters
    #    see transformation html.1::text_delimiters
    inputdata = remove_firstlast_marker(inputdata)

    foot = []
    foot.append("")
    foot.append("</body>")
    foot.append("")
    foot.append("</html>")
    foot = "\n".join(foot)

    return header + inputdata + foot

def output_console(inputdata):
    LOGGER.debug("[D06] [output_console] : data to be read=%s", inputdata)

    # transformation console.1::text_delimiters
    #    let's add a char at the very beginning and at the very end of the
    #    source string.
    inputdata = add_firstlast_marker(inputdata)

    # transformation console.2::maingroup
    inputdata = transf__maingroup(inputdata)

    # transformation console.3::invert_rtltext
    if cfgini.CFGINI["output.console"]["invert_rtltext"].lower() == 'true':
        inputdata = re.sub(globals.RTLREADER_REGEX, transf__invert_rtltext, inputdata)

    # transformation console.4::remove_RTL_SYMBOLS
    # https://en.wikipedia.org/wiki/Bi-directional_text
    if cfgini.CFGINI["output.console"]["rtl symbols"].lower() == "0x200f_0x200e":
        inputdata = inputdata.replace(globals.RTL_SYMBOLS[0], chr(0x200F))
        inputdata = inputdata.replace(globals.RTL_SYMBOLS[1], chr(0x200E))

    elif cfgini.CFGINI["output.console"]["rtl symbols"].lower() == "empty string":
        inputdata = inputdata.replace(globals.RTL_SYMBOLS[0], "")
        inputdata = inputdata.replace(globals.RTL_SYMBOLS[1], "")

    # transformation console.5::undo_text_delimiters
    inputdata = remove_firstlast_marker(inputdata)

    return inputdata

def transf__maingroup(src):
    LOGGER.debug("[D07] transf__maingroup()")

    # transformation maingroup.1::improve_rtlalphatext
    src = transf__improve_rtlalphatext(src)

    # transformation maingroup.2::transf__text_alpha2hebrew
    src = re.sub(globals.RTLREADER_REGEX, transf__text_alpha2hebrew, src)

    # transformation maingroup.3::transf__use_FB1D_FB4F_chars
    src = re.sub(globals.RTLREADER_REGEX, transf__use_FB1D_FB4F_chars, src)

    return src

def check_inputdata(inputdata):
    LOGGER.debug("[D08] check_inputdata()")

    success = True
    errors = []

    # ------------------------------------------------------------------------
    # ---- a special case : no check if RTL_SYMBOLS[0]==RTL_SYMBOLS[1]
    # ------------------------------------------------------------------------
    if globals.RTL_SYMBOLS[0] == globals.RTL_SYMBOLS[1]:
        return True, []

    # ------------------------------------------------------------------------
    # ---- common case : RTL_SYMBOLS[0] != RTL_SYMBOLS[1]
    # ------------------------------------------------------------------------
    # first check : is num_of(globals.RTL_SYMBOLS[0]) equal to num_of(globals.RTL_SYMBOLS[1]) ?
    if inputdata.count(globals.RTL_SYMBOLS[0]) != inputdata.count(globals.RTL_SYMBOLS[1]):
        success = False
        errors.append("Not even numbers of symbols '{0}' and '{1}'".format(globals.RTL_SYMBOLS[0],
                                                                           globals.RTL_SYMBOLS[1]))

    # second check : no two globals.RTL_SYMBOLS[x] twice in a row
    # third check : first RTL_SYMBOL must be globals.RTL_SYMBOLS[0]
    last_symbol = None
    for line_number, line in enumerate(inputdata):
        for char_number, char in enumerate(line):

            context = 'line #{0}::character {1} (\"{2}\")'.format(line_number+1, char_number+1, extract_around_index(line, char_number))

            if char in globals.RTL_SYMBOLS:
                if last_symbol is None:
                    if char == globals.RTL_SYMBOLS[1]:
                        errors.append("first RTL_SYMBOL must be {0}, not {1} (context={2})".format(globals.RTL_SYMBOLS[0],
                                                                                                   globals.RTL_SYMBOLS[1],
                                                                                                   context))
                        success = False
                    else:
                        last_symbol = char
                else:
                    if last_symbol == char:
                        LOGGER.error("[E01] the symbol '%s' appears two times in a row (context=%s)", char, context)
                        success = False
                    last_symbol = char

    return success, errors

##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################

ARGS = read_command_line_arguments()

CFGINI_SUCCESS, CFGERRORS, cfgini.CFGINI = cfgini.read_cfg_file(ARGS.cfgfile)

if not CFGINI_SUCCESS:
    LOGGER.error("[E02] Ill-formed config file '%s' : %s", ARGS.cfgfile, CFGERRORS)
    LOGGER.error("[E03] === program stops ===")
    sys.exit(-1)

READSYMBOLS_SUCCESS, READSYMBOLS_ERRORS, ALPHA2HEBREW, ALPHA2HEBREW_KEYS = read_symbols(ARGS.symbolsfilename)

if not READSYMBOLS_SUCCESS:
    LOGGER.error("[E04] ill-formed symbole file '%s' : %s", ARGS.symbolsfilename, READSYMBOLS_ERRORS)
    LOGGER.error("[E05] === program stops ===")
    sys.exit(-3)

if ARGS.showsymbols:
    for key in ALPHA2HEBREW_KEYS:
        print(stranalyse(key), "---→", stranalyse(ALPHA2HEBREW[key]))

INPUTDATA = ""
if ARGS.source == "inputfile":
    with open(ARGS.inputfile) as inputfile:
        INPUTDATA = inputfile.readlines()
elif ARGS.source == "stdin":
    INPUTDATA = sys.stdin.read()

if ARGS.checkinputdata == 'yes':
    CHECK_SUCCESS, CHECK_ERRORS = check_inputdata(INPUTDATA)
    if not CHECK_SUCCESS:
        LOGGER.error("[E06] Ill-formed input data '%s'; error(s)=%s", ARGS.cfgfile, CHECK_ERRORS)
        LOGGER.error("[E07] === program stops ===")
        sys.exit(-2)

# input > output
if ARGS.transform_alpha2hebrew == 'yes':

    if ARGS.outputformat == 'console':
        print(output_console("".join(INPUTDATA)))
    if ARGS.outputformat == 'html':
        print(output_html("".join(INPUTDATA)))
