Python API reference
====================

This page documents the Python side of the extension, for people who need to
understand how the Fortran directives work, extend them, or use the parser
from a script. Users of the extension only need :doc:`fortran_autodoc` and
:doc:`fortran_domain`.

.. contents:: On this page
   :local:
   :depth: 2


Architecture
------------

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Module
     - Role
   * - :mod:`sphinxfortran_ng.crackfortran_for_sphinx`
     - Trimmed copy of ``numpy.f2py.crackfortran``. Reads Fortran 77/90 files
       and returns a list of *blocks* (dictionaries) describing modules,
       routines, types, interfaces and their variables.
   * - :mod:`sphinxfortran_ng.fortran_autodoc`
     - The class :class:`~sphinxfortran_ng.fortran_autodoc.F90toRst` attaches
       the comments to the blocks and generates reStructuredText; the
       ``f:auto*`` directives call it.
   * - :mod:`sphinxfortran_ng.fortran_domain`
     - The Sphinx domain ``f``: directives, roles, doc fields, index.


Data flow of a build
--------------------

1. ``setup(app)`` of ``fortran_autodoc`` registers the configuration values
   and the ``f:auto*`` directives and connects two handlers to
   ``builder-inited``.
2. :func:`~sphinxfortran_ng.fortran_autodoc.fortran_parse` lists the files
   (:func:`~sphinxfortran_ng.fortran_autodoc.list_files`), builds one
   ``F90toRst`` and stores it in ``app.config._f90torst``.
3. :func:`~sphinxfortran_ng.fortran_autodoc.load_intersphinx_inventories`
   collects the Fortran objects of the Intersphinx inventories.
4. Each ``f:auto*`` directive gets the parser from the configuration,
   generates the text and inserts it in the source of the page
   (``FortranAutoDirective._insert``).
5. The domain directives render that text.

The blocks
~~~~~~~~~~

``crackfortran`` returns one dictionary per top-level unit. The keys used by
``F90toRst`` are:

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Key
     - Content
   * - ``block``
     - ``module``, ``function``, ``subroutine``, ``program``, ``interface``,
       ``type`` or ``use``
   * - ``name``
     - Lower-case name
   * - ``body``
     - Blocks defined inside (routines, types and interfaces of a module)
   * - ``vars``, ``sortvars``
     - Dictionary of the variables, and their names in a sensible order
       (arguments first)
   * - ``args``
     - Names of the dummy arguments of a routine
   * - ``result``
     - Name of the result variable
   * - ``use``
     - Dictionary ``module -> {'map': {remote: local}}`` or ``{}``
   * - ``from``
     - ``file:module`` in which the block was found
   * - ``implementedby``
     - Names of the procedures of an interface
   * - ``bindlang``
     - List of ``(language, name)`` of the ``bind`` clause
   * - ``desc``, ``synopsis``
     - Lists of comment lines added by ``F90toRst.scan``
   * - ``callto``, ``callfrom``
     - Names of the routines called by, and calling, a routine. Added by
       ``F90toRst``

Each variable is itself a dictionary with ``typespec``, ``kindselector`` or
``charselector``, ``attrspec`` (list of attributes), ``dimension``,
``intent``, ``=`` (initial value), and ``desc`` (added by ``F90toRst``).


F90toRst: the key methods
-------------------------

The main entry points, in the order they are used:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Method
     - Purpose
   * - ``__init__(ffiles, ic, ulc, vl, encoding, sst)``
     - Reads and cracks the files, then runs ``build_index``, ``scan`` and
       ``build_callfrom_index``.
   * - ``build_index()``
     - Fills the dictionaries ``modules``, ``types``, ``variables``,
       ``routines`` (also ``functions``, ``subroutines`` and ``interfaces``:
       the same object), ``programs``. Registers the ``use ... only`` aliases
       and builds the regular expressions that find variable descriptions.
   * - ``scan()``
     - Reads the descriptions of all the blocks: ``get_comment`` for the
       header comment, ``_scan_inline_desc`` for the comments of the
       declarations and ``scan_container`` for a routine, program or type.
   * - ``get_blocksrc(block, ...)``
     - Extracts the source lines of a block, with a regular expression for
       its first and last lines.
   * - ``get_comment(src, ...)``
     - Reads the comment that follows the first line of ``src``: the source
       of the rule "comment right after the signature".
   * - ``is_member(block)``
     - Tells if a block is documented, from ``members``, ``undoc_members``,
       ``forceadd_members``, ``exclude_private``.
   * - ``format_module(block)``
     - The text of ``f:automodule``: declaration, description, quick access,
       ``use``, types, variables, routines.
   * - ``format_routine(block)``
     - The text of ``f:autoroutine``: signature, description and the
       ``:p`` / ``:o`` / ``:r`` fields.
   * - ``format_type(block)``, ``format_variable(block)``
     - The text of ``f:autotype`` and ``f:autovariable``.
   * - ``format_variables(module, ownSection)``
     - The text of ``f:automodvars``.
   * - ``format_srcfile(srcfile, ...)``
     - The text of ``f:autosrcfile``.

The attributes that the directives change temporarily are ``ic``
(indentation), ``ulc`` (underline), ``sst`` (``rubric`` or ``title``),
``members``, ``undoc_members``, ``forceadd_members``, ``hide_output`` and
``exclude_private``.

.. code-block:: python

   from sphinxfortran_ng.fortran_autodoc import F90toRst

   f = F90toRst(["examples/SF_ARRAYS.f90"], ic="   ")
   f.members = "linspace,arange"       # like ``:members: linspace, arange``
   print(f.format_module("sf_arrays"))

Formatting helpers
~~~~~~~~~~~~~~~~~~

``format_argtype``, ``format_argdim`` and ``format_argattr`` produce the three
parts of a field name; ``format_argfield`` and ``format_interfacearg``
assemble the ``:p`` / ``:o`` / ``:r`` / ``:f`` fields; ``format_signature``
and ``format_interface`` write the arguments of a signature;
``format_use`` writes the ``use`` statements; ``format_funcref`` writes a
cross-reference to a routine, a type or a variable, with the module and
the aliases.


Reference
---------

.. automodule:: sphinxfortran_ng.fortran_autodoc
   :members:
   :undoc-members:

.. automodule:: sphinxfortran_ng.fortran_domain
   :members:
   :undoc-members:


