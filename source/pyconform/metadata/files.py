"""
File Metadata Class

Copyright 2017-2018, University Corporation for Atmospheric Research
LICENSE: See the LICENSE.rst file for details
"""


class File(object):
    """
    Metadata describing a NetCDF file
    """

    def __init__(self, name):
        self.name = name
        self.attributes = {}
        self.deflate = 1
