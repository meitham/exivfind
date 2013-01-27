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

import fnmatch
import hashlib
import os
import traceback

try:
    import ipdb as pdb
except ImportError:
    import pdb

import pyexiv2

from pygnutools import Primary, PrimaryAction


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
        tag_name = context['args'][0]
        tag_value = context['args'][1]
        verbosity = context.get('verbosity', 0)
        exiv_tag = exiv_tags.get(tag_name, tag_name)
        try:
            metadata = context['exif.metadata']
        except KeyError:
            metadata = read_exiv(path, verbosity)
            context['exif.metadata'] = metadata
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


class PrintBufferHashPrimary(Primary):
    """Print a hash of the main image buffer
    """
    def __call__(self, context):
        path = context['path']
        tag_name = context['args']
        verbosity = context.get('verbosity', 0)
        try:
            metadata = context['metadata']
        except KeyError:
            metadata = read_exiv(path, verbosity)
            context['exif.metadata'] = metadata
        if metadata is None:
            return context
        h = hashlib.sha256()
        h.update(metadata.buffer)
        digest = h.hexdigest()
        context['buffer'].append(digest)
        return context


class PrintTagPrimary(Primary):
    """Print a tag by name
    Always return context
    """
    def __call__(self, context):
        path = context['path']
        tag_name = context['args']
        verbosity = context.get('verbosity', 0)
        tag_name = exiv_tags.get(tag_name, tag_name)
        try:
            m = context['metadata']
        except KeyError:
            m = read_exiv(path, verbosity)
            context['exif.metadata'] = m
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
        try:
            m = context['metadata']
        except KeyError:
            m = read_exiv(path, verbosity)
            context['exif.metadata'] = m
        if m is None:
            return context
        if tag_name is not None:
            tags = [(k, m[k].raw_value) for k in fnmatch.filter(m.exif_keys, tag_name)]
        else:
            tags = [(k, m[k].raw_value) for k in m.exif_keys]
        pairs = ["%(k)s: %(v)s" % {'k': k, 'v': v} for k, v in tags]
        context['buffer'].append('\n'.join(pairs))
        return context


primaries_map = {
        'tag': TagMatchPrimary(case_sensitive=True),
        'make': TagMatchPrimary(case_sensitive=True, tag_name='make'),
        'imake': TagMatchPrimary(case_sensitive=False, tag_name='make'),
        'model': TagMatchPrimary(case_sensitive=True, tag_name='model'),
        'imodel': TagMatchPrimary(case_sensitive=False, tag_name='imodel'),
        'software': TagMatchPrimary(case_sensitive=True, tag_name='software'),
        'isoftware': TagMatchPrimary(case_sensitive=False, tag_name='software'),
        'print_tag': PrintTagPrimary(),
        'print_tags': PrintTagsPrimary(),
        'print_buffer_hash': PrintBufferHashPrimary(),
#        'orientation': orientation,
#        'date-time': exiv_datetime,
#        'date-time-newer': exiv_datetime_newer,
#        'compression': compression,
#        'x-resolution': x_resolution,  # accepts expressions e.g. ">3000"}
}


def cli_args(parser):
    """This will be called by the main cli_args() from pygnutools
    """
    parser.add_argument('-tag', dest='tag', action=PrimaryAction,
            nargs=2,
            help="""Filter images by a tag and its value
            """)
    parser.add_argument('-make', dest='make', action=PrimaryAction,
            help="""Filter images by their camera manufacterer name.
            e.g. `-make Canon`
            would only match images where Exif.Image.Make is "Canon"
            """)
    parser.add_argument('-imake', dest='imake', action=PrimaryAction,
            help="""Filter images by their camera manufacterer name.
            similar to `-make` except this match is case insensitive
            e.g. `-imake canon`
            would match images where Exif.Image.Make is "Canon" or "CaNoN"
            """)
    parser.add_argument('-model', dest='model', action=PrimaryAction,
            help="""Filter images by their camera manufacterer model.
            """)
    parser.add_argument('-imodel', dest='imodel', action=PrimaryAction,
            help="""Filter images by their camera manufacterer model.
            This match is case insensitive.
            """)
    parser.add_argument('-software', dest='software', action=PrimaryAction,
            help="""Filter images by Exif.Image.Software value.
            """)
    parser.add_argument('-isoftware', dest='isoftware', action=PrimaryAction,
            help="""Filter images by Exif.Image.Software value.
            This match is case insensitive.
            """)
    parser.add_argument('-print-buffer-hash', dest='print_buffer_hash',
            action=PrimaryAction, nargs=0, help="""Print a hash of the image
            buffer.
            """)
    parser.add_argument('-print-tag', dest='print_tag', action=PrimaryAction,
            help="""Print a tag given by name.
            e.g. `-print-tag "Exif.Thumbnail.Orientation"`
            You could also use short version of the tag,
            e.g. `-print-tag "make"` would resolve to "Exif.Image.Make"
            The argument here could be a pattern (follows unix globbing
            patterns) so you could say
            `-print-tag '*Image*'` and that would match any tag that contains
            the work "Image", case sensitive.
            """)
    parser.add_argument('-print-tags', dest='print_tags',
            action=PrimaryAction, nargs='?',
            help="""Print a tag given by name.
            similar to -print-tag except this would print the actual tag name
            before the tag value, separated by a colon.
            The argument here is optional and if no argument provided then it
            would print all tags available in the image metadata.
            """)
    return parser


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

