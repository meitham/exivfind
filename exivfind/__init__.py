#!/usr/bin/env python
"""
TODO:
    4. provide more tests such as
        a. -has-tag "tag_name"
        b. -ihas-tag "tag_name"  # case insensetive
        c. -rhas-tag "tag_name"  # regex
        The tags above can optional take a value
    5. Supports files as arguments.
"""
from __future__ import print_function

import os
import traceback
import fnmatch

try:
    import ipdb as pdb
except ImportError:
    import pdb

from pygnutools import Primary, PrimaryAction
import pyexiv2
from functools32 import lru_cache


exiv_tags = {
        'make': 'Exif.Image.Make',
        'model': 'Exif.Image.Model',
        'software': 'Exif.Image.Software',
}


class TagMatchPrimary(Primary):
    """Matches an exiv tag from a file against a porposed one from a user
    """
    def __call__(self, context):
        path = context['path']
        tag_name = self.tag_name
        tag_value = context['args']
        verbosity = context.get('verbosity', 0)
        exiv_tag = exiv_tags.get(tag_name, tag_name)
        metadata = read_exiv(path, verbosity)
        if metadata is None:
            return
        try:
            exiv_tag_value = metadata[exiv_tag].value
            if not self.case_sensitive:
                tag_value = tag_value.lower()
                exiv_tag_value = exiv_tag_value.lower()
            if tag_value == exiv_tag_value:
                return context
            return
        except KeyError:  # tag is not available
            if verbosity > 2:
                traceback.print_exc()
            return None


class PrintTagPrimary(Primary):
    """Print a tag by name
    Always return context
    """
    def __call__(self, context):
        path = context['path']
        tag_name = context['args']
        verbosity = context.get('verbosity', 0)
        tag_name = exiv_tags.get(tag_name, tag_name)
        m = read_exiv(path, verbosity)
        if m is None:
            return context
        try:
            exiv_tag_value = m[tag_name].raw_value
            context['buffer'].append(exiv_tag_value)
            return context
        except KeyError:
            pass
        tags = [m[k].raw_value for k in fnmatch.filter(m.exif_keys, tag_name)]
        if tags:
            context['buffer'].append('\n'.join(tags))
        return context


class PrintTagsPrimary(Primary):
    """Print all tags available in an image
    Always return context
    """
    def __call__(self, context):
        path = context['path']
        tag_name = context.get('args', None)
        verbosity = context.get('verbosity', 0)
        m = read_exiv(path, verbosity)
        if m is None:
            return context
        tags = [m[k].raw_value for k in fnmatch.filter(m.exif_keys, tag_name)]
        pairs = ["%(k)s: %(v)s" % {'k': k, 'v': m[k].raw_value} for k in tags]
        context['buffer'].append('\n'.join(pairs))
        return context


primaries_map = {
        'tag': TagMatchPrimary(case_sensitive=True),
        'make': TagMatchPrimary(case_sensitive=True, tag_name='make'),
        'imake': TagMatchPrimary(case_sensitive=False, tag_name='make'),
        'software': TagMatchPrimary(case_sensitive=True, tag_name='software'),
        'isoftware': TagMatchPrimary(case_sensitive=False, tag_name='software'),
        'print_tag': PrintTagPrimary(),
        'print_tags': PrintTagsPrimary(),
#        'make': partial(tag_match, tag='make'),
#        'imake': partial(tag_match, tag='make', case_sensitive=False),
#        'model': partial(tag_match, tag='model'),
#        'imodel': partial(tag_match, tag='model', case_sensitive=False),
#        'rmake': rmake,
#        'orientation': orientation,
#        'software': partial(tag_match, tag='software'),
#        'date-time': exiv_datetime,
#        'date-time-newer': exiv_datetime_newer,
#        'compression': compression,
#        'x-resolution': x_resolution,  # accepts expressions e.g. ">3000"}
}


def cli_args(parser):
    """This will be called by the main cli_args() from pygnutools
    """
    parser.add_argument('-make', dest='make', action=PrimaryAction)
    parser.add_argument('-imake', dest='imake', action=PrimaryAction)
    parser.add_argument('-model', dest='model', action=PrimaryAction)
    parser.add_argument('-imodel', dest='imodel', action=PrimaryAction)
    parser.add_argument('-software', dest='software', action=PrimaryAction)
    parser.add_argument('-isoftware', dest='isoftware', action=PrimaryAction)
    parser.add_argument('-print-tag', dest='print_tag', action=PrimaryAction)
    parser.add_argument('-print-tags', dest='print_tags',
            action=PrimaryAction, nargs='?')
    return parser


@lru_cache(maxsize=128)
def read_exiv(path, verbosity=0):
    """Returns an EXIF metadata from a file
    """
    try:
        metadata = pyexiv2.ImageMetadata(path)
        metadata.read()
        return metadata
    except(IOError, UnicodeDecodeError) as e:
        if verbosity > 1:
            traceback.print_exc()
        return None

