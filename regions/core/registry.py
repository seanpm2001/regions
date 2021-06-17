# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
This module provides a RegionsRegistry class.
"""

from astropy.table import Table

__all__ = []


class IORegistryError(Exception):
    """Exception class for various registry errors."""


class RegionsRegistry:
    """
    Class to hold a registry to read, write, parse, and serialize regions
    in various formats.
    """

    registry = {}

    @classmethod
    def register(cls, classobj, methodname, filetype):
        def inner_wrapper(wrapped_func):
            key = (classobj, methodname, filetype)
            if key in cls.registry:
                raise ValueError(f'{methodname} for {filetype} is already '
                                 f'registered for {classobj.__name__}')
            cls.registry[key] = wrapped_func
            return wrapped_func
        return inner_wrapper

    @classmethod
    def get_identifiers(cls, classobj):
        return [key for key in cls.registry
                if key[0] == classobj and key[1] == 'identify']

    @classmethod
    def identify_format(cls, filename, classobj, methodname):
        format = None
        identifiers = cls.get_identifiers(classobj)
        if identifiers:
            for identifier in identifiers:
                if cls.registry[identifier](methodname, filename):
                    format = identifier[2]
                    break  # finds the first valid filetype

        if format is None:
            msg = ('Format could not be identified based on the file name or '
                   'contents, please provide a "format" argument.'
                   f'\n{cls._get_format_table_str(classobj)}')
            raise IORegistryError(msg)

        return format

    @classmethod
    def read(cls, filename, classobj, format=None, **kwargs):
        """
        Read in a regions file.
        """
        if format is None:
            format = cls.identify_format(filename, classobj, 'read')
        key = (classobj, 'read', format)
        try:
            return cls.registry[key](filename, **kwargs)
        except KeyError:
            msg = (f'No reader defined for format "{format}" and class '
                   f'"{classobj.__name__}".\n'
                   f'{cls._get_format_table_str(classobj)}')
            raise IORegistryError(msg) from None

    @classmethod
    def parse(cls, data, classobj, format=None, **kwargs):
        """
        Parse a regions string or table.
        """
        key = (classobj, 'parse', format)
        return cls.registry[key](data, **kwargs)

    @classmethod
    def write(cls, regions, filename, classobj, format=None, **kwargs):
        """
        Write to a regions file.
        """
        if format is None:
            format = cls.identify_format(filename, classobj, 'write')
        key = (classobj, 'write', format)
        return cls.registry[key](regions, filename, **kwargs)

    @classmethod
    def serialize(cls, regions, classobj, format=None, **kwargs):
        """
        Serialize to a regions string or table.
        """
        key = (classobj, 'serialize', format)
        return cls.registry[key](regions, **kwargs)

    @classmethod
    def get_formats(cls, classobj):
        """
        Get the registered I/O formats as a Table.
        """
        filetypes = list({key[2] for key in cls.registry
                          if key[0] == classobj})

        rows = [['Format', 'Parse', 'Serialize', 'Read', 'Write',
                 'Auto-identify']]
        for filetype in sorted(filetypes):
            keys = {key[1] for key in cls.registry
                    if key[0] == classobj and key[2] == filetype}
            row = [filetype]
            for methodname in rows[0][1:]:
                name = ('identify' if 'identify' in methodname
                        else methodname.lower())
                row.append('Yes' if name in keys else 'No')
            rows.append(row)

        if len(rows) == 1:
            return ''

        cols = list(zip(*rows))
        tbl = Table()
        for col in cols:
            tbl[col[0]] = col[1:]

        return tbl

    @classmethod
    def _get_format_table_str(cls, classobj):
        lines = ['', f'The available formats for the {classobj.__name__} '
                 'class are:', '']
        tbl = cls.get_formats(classobj)
        lines.extend(tbl.pformat(max_lines=-1, max_width=80))
        return '\n'.join(lines)
