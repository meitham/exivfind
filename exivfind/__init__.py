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

try:
    import ipdb as pdb
except ImportError:
    import pdb

from pygnutools import Primary
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
        fname = context['fname']
        fpath = context['fpath']
        tag_name = context['args1']
        tag_value = context['args2']
        exiv_tag = exiv_tags.get(tag_name, tag_name)
        metadata = read_exiv(fpath, fname, verbosity)
        if metadata is None:
            return
        try:
            exiv_tag_value = metadata[exiv_tag].value
            if verbosity > 2:
                print("%(exiv_tag)s: %(exiv_tag_value)s" % locals())
            if self.case_sensitive:
                tag_value, exiv_tag_value = map(lower,
                        [tag_value, exiv_tag_value])
            if user_tag_value == exiv_tag_value:
                return context
            return
        except KeyError:  # tag is not available
            if verbosity > 2:
                traceback.print_exc()
            return None


primaries_map = {
        'tag': TagMatchPrimary(case_sensitive=True),
#        'print_tag': act_print_tag,
#        'print_all_tags': act_print_all_tags,
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


def act_print_tag(fpath, fname, *args, **kwargs):
    verbosity = kwargs.get('verbosity', 0)
    tag = kwargs['print_tag']
    metadata = read_exiv(fpath, fname, verbosity)
    try:
        exiv_tag = exiv_tags[tag]
    except KeyError:
        exiv_tag = tag
    if metadata is None:
        return
    try:
        exiv_tag_value = metadata[exiv_tag].value
        print(exiv_tag_value)
    except KeyError:  # tag is not available
        if verbosity > 2:
            traceback.print_exc()


def act_print_all_tags(fpath, fname, *args, **kwargs):
    verbosity = kwargs.get('verbosity', 0)
    metadata = read_exiv(fpath, fname, verbosity)
    if not metadata:
        return
    for k in metadata.exif_keys:
        print("%(k)s: %(v)s" % {'k': k, 'v': metadata[k].raw_value})


def cli_args(parser):
    """This will be called by the main cli_args() from pygnutools
    """
    parser.add_argument('-make', dest='make', action=TestAction)
    parser.add_argument('-imake', dest='imake', action=TestAction)
    parser.add_argument('-model', dest='model', action=TestAction)
    parser.add_argument('-imodel', dest='imodel', action=TestAction)
    parser.add_argument('-true', dest='true', action=TestAction, nargs=0)
    parser.add_argument('-print-tag', dest='print_tag', action=ActionAction)
    parser.add_argument('-print-all-tags', dest='print_all_tags',
            action=ActionAction, nargs=0)
    return parser


@lru_cache(maxsize=128)
def read_exiv(fpath, fname, verbosity=0):
    """Returns an EXIF metadata from a file
    """
    path = os.path.join(fpath, fname)
    try:
        metadata = pyexiv2.ImageMetadata(path)
        metadata.read()
        return metadata
    except(IOError, UnicodeDecodeError) as e:
        if verbosity > 1:
            traceback.print_exc()
        return None
