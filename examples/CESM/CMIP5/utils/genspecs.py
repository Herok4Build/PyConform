#!/usr/bin/env python
"""
genspecs

Command-Line Utility to generate specfiles from a set of "correct" output files

Copyright 2017, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""

from glob import glob
from os import listdir, linesep
from os.path import isdir, join as pjoin
from argparse import ArgumentParser

__PARSER__ = ArgumentParser(description='Create a specfile from a set of output files')
__PARSER__.add_argument('-o', '--output', help='Name of the output specfile')
__PARSER__.add_argument('root', help='Root directory where output files can be found')

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

    ROOT = args.root.rstrip('/')
    if not isdir(ROOT):
        raise ValueError('Root must be a directory')

    # Assume that ROOT directory is of the form:
    # ROOT = <root>/<institution>/<model>
    root, inst, model = ROOT.rsplit('/', 2)
    
    # Check for consistency
    if inst != 'NCAR' and model != 'CCSM4':
        raise ValueError('Root appears to be malformed')
    
    print 'Institution: {}'.format(inst)
    print 'Model: {}'.format(model)
    print
    
    # Fill out a dictionary of experiment:table:variables
    mipvars = {expt:{} for expt in listdir(ROOT)}
    for expt in mipvars:
        print 'Experiment: {}'.format(expt)
        for freq in listdir(pjoin(ROOT, expt)):
            print '  Frequency: {}'.format(freq)
            for realm in listdir(pjoin(ROOT, expt, freq)):
                print '    Realm: {}'.format(realm)
                for table in listdir(pjoin(ROOT, expt, freq, realm)):
                    print '      Table: {}'.format(table)
                    
                    if table not in mipvars[expt]:
                        mipvars[expt] = {table: set()}

                    # Pick an ensemble member (doesn't matter which)
                    ens = listdir(pjoin(pjoin(ROOT, expt, freq, realm, table)))[0]
    
                    # Find list of all latest-version variables
                    vars = listdir(pjoin(ROOT, expt, freq, realm, table, ens, 'latest'))
                    
                    # Add vars to table
                    for var in vars:
                        mipvars[expt][table].add(var)

                    print '        Vars: {}'.format(','.join(sorted(mipvars[expt][table])))

    print mipvars
    
    

#===================================================================================================
# Command-line Operation
#===================================================================================================
if __name__ == '__main__':
    main()
