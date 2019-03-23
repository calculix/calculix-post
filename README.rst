Post-processing for expanded elements in Calculix
#################################################

:date: 2019-03-23
:tags: calculix, Python 3
:author: Roland Smith

.. Last modified: 2019-03-23T14:29:13+0100

Introduction
------------

Calculix_ expands 2D shell elements into 3D elements. For example, ``S6``
elements are expanded into ``C3D15`` elements.

.. _Calculix: http://www.calculix.de/

Before Calculix 2.15, that expansion was printed to standard output. From 2.15
it is captured in a ``.12d`` file.

The reporting in the ``frd`` file does not contain the expanded elments.
This has no consequence for the displacements; they will still be reported
properly. But the stresses and strains in the expanded elements are averaged
when reported in 2D form. This means that bending stresses and strains are not
reported properly.


How does it work
----------------

The purpose of this program is to read the ``.12d`` file and the ``.dat``
file, and insert the displacements for the expanded nodes into the ``.frd``
file.

At this moment it only works for ``S6`` elements, expanded into ``C3D15``.

Note that currently the expansion is simple and crude. The displacements of
the original nodes from the 2D S6 elements are simply copied to the correct
expanded nodes.

It should be slightly more accurate to calculate a normal vector of the
displaced element, and use that (scaled to 1/2 the element's thickness) to
create the offset displacments. This might be implemented later.


Calculix input file
-------------------

The calculix input file should contain the following::

    *NODE FILE,OUTPUT=3D,NSET=Nall
    U,RF
    *NODE PRINT,NSET=Nall
    U

* The ``OUTPUT=3D`` option in the ``*NODE FILE`` card is required for element expansion.
* The ``U`` belonging to the ``*NODE FILE`` card is required to make sure that
  the header for the displacements is present in the ``.frd`` results file.
  This is necessary for splicing in the displacments later.
* The ``*NODE PRINT`` card followed by ``U`` is required so that the expanded
  node displacements are written to a ``.dat`` file.


Invocation
----------

After running calculix, the program should be started from the directory that
contains the results.

.. code-block:: console

    python3 post.py <foo>

Where ``<foo>`` is the name of the input and output files *without extension*.
After the run, the amended results are found in a file ``<foo>-post.frd``.
