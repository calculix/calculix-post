# file: post.py
# vim:fileencoding=utf-8:fdm=marker:ft=python
#
# Copyright © 2019 R.F. Smith <rsmith@xs4all.nl>.
# SPDX-License-Identifier: MIT
# Created: 2019-03-16T23:08:29+0100
# Last modified: 2019-03-23T13:12:42+0100
"""Post-process OUTPUT=3D data to generate proper node displacement.

This is used when the card *NODE FILE,OUTPUT=3D is used. That output format
does *not* output displacements when specified.

Instead, add a *NODE PRINT,NSET=Nall for displacement. This script then pulls
the displacement data from the .dat file, and the link between original and
expanded elements from the log file.

Usage: “python3 post.py <basename>”
"""

import sys
import types


def read_displacements(base):
    """
    Read the original node displacements from the <base>.dat file. Assumes that the
    displacement is followed by the internal energy.

    That is, that the input file contains the following:

        *NODE PRINT,NSET=Nall
        U
        *EL PRINT,ELSET=Eall
        ELSE

    Arguments:
        base: string containing the base name of the “.dat” file.

    Returns:
        A tuple of 3-tuples containing the x, y and z displacements of each node.
        Note that while tuple offsets start at 0, node numbers start at 1!
    """
    with open(base+'.dat') as dat:
        lines = [ln.strip() for ln in dat.readlines()]
    # Get the index from the beginning of the “energy” lines.
    start = [n for n, ln in enumerate(lines) if 'energy' in ln][0] + 2
    # Read the original displacements.
    end = start - 3
    start = [n for n, ln in enumerate(lines) if 'displacements' in ln][0] + 2
    disp = [tuple(float(j) for j in ln.split()[1:]) for ln in lines[start:end]]
    # Return the original displacements.
    return tuple(disp)


def read_expansion(base):
    """
    Read the <base>.12d calculix output file and extract the mapping from flat
    to expanded elements. Requires calculix 2.15.

    Arguments:
        base: string containing the base name of the “.12d” file.

    Returns:
        A tuple of types.SimpleNamespace. Each of those contains;
        * An integer named “element” containing the element number.
        * A tuple of integers named “orig” containing the original node numbers.
        * A tuple of integers named “new” containing the expanded node numbers.

    Note that node and element numbers in calculix start with 1.
    """
    with open(base+'.12d') as dat:
        lines = [ln.strip() for ln in dat.readlines()]
    indices = [n for n, ln in enumerate(lines) if ln.startswith('ELEMENT')]
    rv = []
    for i in indices:
        d = types.SimpleNamespace()
        d.element = int(lines[i].split()[1])
        d.orig = tuple(int(i) for i in lines[i+1].split())
        d.new = (tuple(int(i) for i in lines[i+3].split()) +
                 tuple(int(i) for i in lines[i+4].split()))
        rv.append(d)
    return tuple(rv)


def new_displacements(orig, expansion):
    """
    Calculate the new displacements from the original displacements
    and the expansion.

    The algorithm in this implementation is simple and crude;
    It just copies the displacements from the original nodes to the new nodes.
    It does *not* transform the points.

    TODO: implement proper transformation of the expanded node displacments.
    Note that the element thickness needs to be known to do this!

    Arguments:
        orig: A tuple of 3-tuples containing the displacements of each original node.
        expansion: A tuple of types.SimpleNamespace containing the original and
            expanded nodes.

    Returns:
        A tuple of 2-tuples (node, (dx, dy, dz)).
    """
    # This maps the expanded element node numbers to the original node
    # numbers.
    mapping = {
        0: 0, 1: 1,  2: 2,  3: 0,  4: 1,  5: 2,  6: 3, 7: 4,
        8: 5, 9: 3, 10: 4, 11: 5, 12: 0, 13: 1, 14: 2
    }
    newdisp = {}
    for e in expansion:
        org, new = e.orig, e.new
        for x, n in enumerate(new):
            if n not in newdisp:
                newdisp[n] = orig[org[mapping[x]]-1]
    idx = sorted(list(newdisp.keys()))
    return tuple((i, newdisp[i]) for i in idx)


def splice(base, new):
    """
    Splice the new displacements into the .frd file.
    """
    with open(base+'.frd') as dat:
        lines = [ln for ln in dat.readlines()]
    idx = [n for n, ln in enumerate(lines) if 'DISP' in ln][0] + 5
    # Check:
    if not lines[idx].strip().startswith('-3'):
        raise ValueError(f'wrong offset: {idx}')
    splice = []
    for node, (dx, dy, dz) in new:
        splice.append(f' -1{node:>10d}{dx: 11.5E}{dy: 11.5E}{dz: 11.5E}\n')
    before = lines[:idx]
    after = lines[idx:]
    total = before + splice + after
    with open(base+'-post.frd', 'wt') as newdat:
        newdat.writelines(total)


def main(argv):
    """
    Entry point for post.py.

    Arguments:
        argv: command line arguments
    """
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    orig_disp = read_displacements(sys.argv[1])
    expansion = read_expansion(sys.argv[1])
    new = new_displacements(orig_disp, expansion)
    splice(sys.argv[1], new)


if __name__ == '__main__':
    main(sys.argv[1:])
