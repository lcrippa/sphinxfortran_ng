Quick start
===========

This page goes from an empty Sphinx project to a rendered Fortran module in
five steps.


Installation
------------

.. code-block:: console

   $ pip install sphinxfortran_ng

The extension requires Python 3.8 or later and Sphinx. From a repository
checkout, use ``pip install -e .`` instead. To build *this* documentation,
install the requirements of the ``doc`` folder:

.. code-block:: console

   $ pip install -r doc/requirements.txt
   $ sphinx-build -b html doc doc/_build/html


Configuring ``conf.py``
-----------------------

Both extensions must be listed. The domain (``sphinxfortran_ng.fortran_domain``)
creates the ``f:`` domain; the autodoc extension only *adds* its directives to
it, so it does nothing on its own.

.. code-block:: python

   extensions = [
       "sphinxfortran_ng.fortran_domain",
       "sphinxfortran_ng.fortran_autodoc",
   ]

   # Where to look for Fortran sources: files, glob patterns or directories
   fortran_src = ["../src"]

   # Extensions searched in directories (case does not matter)
   fortran_ext = ["f90", "f95", "f03"]

The complete list of configuration values is given in
:ref:`autodoc-config`.

.. note::

   Directories in ``fortran_src`` are **not** searched recursively. Add one
   entry per directory, or use a glob such as ``"../src/*/*.f90"``.


Commenting the source
---------------------

Write the description **inside** the documented block, on the comment lines
that immediately follow its first line, and describe each variable with a
comment at the end of its declaration:

.. code-block:: fortran

   subroutine scale(x, factor)
   !Multiplies :f:var:`x` in place by :f:var:`factor`.
     real(8), intent(inout)  :: x(:)   !Array to scale
     real(8), intent(in)     :: factor !Multiplicative factor
     x = x * factor
   end subroutine scale

There is no ``!>`` / ``!!`` marker: those characters would be copied into the
output. The full rules are in :doc:`how_to_comment`.


Using the directives
--------------------

In any ``.rst`` file, document a whole module:

.. code-block:: rst

   .. f:automodule:: mymodule

or pick individual objects:

.. code-block:: rst

   .. f:autoroutine:: mymodule/scale

   .. f:autotype:: mytype

   .. f:autovariable:: beta

See :doc:`fortran_autodoc` for every directive and option.


Cross-referencing
-----------------

Anywhere in the documentation, whether in an ``.rst`` file or inside a
Fortran comment:

.. code-block:: rst

   See :f:mod:`mymodule`, :f:func:`scale`, :f:var:`beta` and :f:type:`mytype`.

Roles are listed in :ref:`domain-roles`.


Rebuilding after a Fortran change
---------------------------------

The Fortran files are parsed once, when the builder starts, but they are not
registered as dependencies of the pages that use them. If you only edit a
``.f90`` file, an incremental ``sphinx-build`` will consider the ``.rst``
pages up to date and skip them. Force a full re-read with:

.. code-block:: console

   $ sphinx-build -E -b html doc doc/_build/html

(or delete the ``_build`` folder, or ``touch`` the ``.rst`` page).
