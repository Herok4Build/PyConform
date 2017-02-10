#!/usr/bin/env python
"""
cmip5_patterns

Command-Line Utility to analyze file-directory patterns in CMIP5 data

Copyright 2017, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from glob import glob
from os import listdir, linesep
from os.path import isfile, join as pjoin
from argparse import ArgumentParser

__PARSER__ = ArgumentParser(description='Analyze file-directory patters of CMIP5 data')
__PARSER__.add_argument('patterns', help='The text file containing all file-directory patterns')

#===================================================================================================
# cli - Command-Line Interface
#===================================================================================================
def cli(argv=None):
    """
    Command-Line Interface
    """
    return __PARSER__.parse_args(argv)


#===================================================================================================
# main - Main Program
#===================================================================================================
def main(argv=None):
    """
    Main program
    """
    args = cli(argv)

    if not isfile(args.patterns):
        raise ValueError('Patterns file not found')

    # Read the patterns file
    with open('cmip5_patterns.txt') as f:
        ncvars = [line.split() for line in f]
                    
    # Analyze freq/realm/table correlations
    frtcorr = {}
    for ncvar in ncvars:
        frt = tuple(ncvar[1:4])
        table = frt[-1]
        if table in frtcorr:
            frtcorr[table].add(frt)
        else:
            frtcorr[table] = {frt}

    print
    print 'Tables with multiple freq/realm/table patterns:'
    for table in frtcorr:
        if len(frtcorr[table]) > 1:
            print "  Table {}:  {}".format(table,', '.join('/'.join(frt) for frt in frtcorr[table]))
    
    # Analyze freq/table correlations
    ftcorr = {}
    for ncvar in ncvars:
        ft = tuple(ncvar[1:4:2])
        table = ft[-1]
        if table in ftcorr:
            ftcorr[table].add(ft)
        else:
            ftcorr[table] = {ft}

    print
    print 'Tables with multiple freq/table patterns:'
    for table in ftcorr:
        if len(ftcorr[table]) > 1:
            print "  Table {}:  {}".format(table,', '.join('/'.join(ft) for ft in ftcorr[table]))
    
        

#===================================================================================================
# Command-line Operation
#===================================================================================================
if __name__ == '__main__':
    main()
