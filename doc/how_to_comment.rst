Formatting Fortran (.f90) Code for Auto-Documentation
=====================================================

This document describes how a Fortran 90 source file must be formatted so it
can be automatically documented by the Fortran Sphinx domain. Every rule below
was checked against the parser, and every "generated output" block is what
``f:automodule`` / ``f:autoroutine`` really produce for the snippet above it.

.. contents:: On this page
   :local:
   :depth: 2


General Rules
-------------

* Documentation is extracted from ordinary Fortran comments (``!``). **No
  special marker is needed.** In particular ``!>`` and ``!!`` (Doxygen style)
  are *not* recognised and would be copied literally into the output.
* The description of a module, function, subroutine, interface, derived type
  or program is the block of comment lines **immediately following its opening
  statement**, i.e. *inside* the entity, before any ``use``, ``implicit none``
  or declaration.
* The description of a variable, argument or derived-type component is the
  comment written **at the end of its declaration line**, optionally followed
  by continuation comment lines.
* Comments are written in **reStructuredText**, so lists, math, admonitions and
  cross-reference roles all work.
* Everything that can be deduced from the code is taken from the code: names,
  order of arguments, types, kinds of character strings, array shapes,
  ``intent``, ``optional``, ``parameter``, default values from initialisers,
  ``bind(c)`` bindings, ``use`` statements. Do not repeat it in the comments.

The single most frequent mistake is to write the comment *before* the entity,
as in Doxygen or Python. The parser never looks there:

.. code-block:: fortran

   !> Computes the double of x.
   !! (comment placed BEFORE the routine)
   function twice(x) result(y)
     real(8) :: x  !Input value
     real(8) :: y  !Twice x
     y = 2*x
   end function twice

produces no description at all:

.. code-block:: rst

   .. f:function:: twice(x)

      :p real x: Input value
      :r real y: Twice x

whereas the same comment moved one line down is picked up:

.. code-block:: fortran

   function twice(x) result(y)
   !Computes the double of x.
     real(8) :: x  !Input value
     real(8) :: y  !Twice x
     y = 2*x
   end function twice

.. code-block:: rst

   .. f:function:: twice(x)

      Computes the double of x.

      :p real x: Input value
      :r real y: Twice x


Modules
-------

The comment lines directly under the ``module`` statement form the module
description. A line whose text starts with ``:synopsis:`` is not part of the
description: it becomes the one-line summary displayed in the module index
(and in the ``:synopsis:`` option of ``f:module``).

.. code-block:: fortran

   module m
   !:synopsis: Short text shown in the module index
   !Long description of the module, with rst markup:
   !
   ! * first point
   ! * second point
     implicit none
     real(8) :: pi  !Circle constant
   end module m

generates

.. code-block:: rst

   .. f:module:: m
      :synopsis: Short text shown in the module index

   .. rubric:: Description

   Long description of the module, with rst markup:

    * first point
    * second point

   .. rubric:: Quick access

   :Variables: :f:var:`pi`

   .. rubric:: Variables

   .. f:variable:: pi

      Circle constant

      :Type: real

Without a ``:synopsis:`` line, the synopsis is the first paragraph of the
description (at most the first four lines). ``ED_INPUT_VARS`` (see
:doc:`examples`) starts like this:

.. code-block:: fortran

   MODULE ED_INPUT_VARS
     !:synopsis: User-accessible input variables
     !Contains all global input variables which can be set by the user through the input file.
     !...
     !
     USE SF_VERSION
     USE SF_PARSE_INPUT
     ...

The ``use`` statements are listed automatically under *Used modules* (for the
modules that are themselves documented in the project) and *External modules*
(for the others), together with the ``only`` lists and renamings.

.. note::

   Preprocessor directives such as ``#ifdef _MPI`` are not evaluated: the
   modules used in *all* the branches are listed (this is why ``mpi`` and
   ``sf_mpi`` appear in the ``use`` field of ``ed_read_input``).


Functions and Subroutines
-------------------------

A routine is documented by:

1. a description block right under its signature line;
2. one comment at the end of the declaration of each argument, and of the
   result variable of a function.

Here is ``linspace`` of ``SF_ARRAYS`` (shortened):

.. code-block:: fortran

   function linspace(start,stop,num,istart,iend,mesh) result(array)
   !
   !Returns an array of evenly spaced numbers over a specified interval.
   !Returns :f:var:`num` evenly spaced samples, calculated over the interval [:f:var:`start`, :f:var:`stop`].
   !The start and end points of the interval can optionally be excluded.
   !
     real(8)          :: start       !Starting value of the sequence
     real(8)          :: stop        !End value of the sequence
     integer          :: num         !Number of samples to generate
     logical,optional :: istart      !If :code:`.true.`, :f:var:`start` is included in the resulting array. Default :code:`.true.`
     logical,optional :: iend        !If :code:`.true.`, :f:var:`stop` is included in the resulting array. Default :code:`.true.`
     real(8),optional :: mesh        !If present, the step is saved in this variable
     real(8)          :: array(num)  !Contains :f:var:`num` equally spaced samples in the interval 
                                     ![:f:var:`start`, :f:var:`stop`], left/right open or closed depending on 
                                     !:f:var:`istart` and :f:var:`iend`
     ...

The generated text is:

.. code-block:: rst

   .. f:function:: linspace(start, stop, num[, istart, iend, mesh])

      Returns an array of evenly spaced numbers over a specified interval.
      Returns :f:var:`num` evenly spaced samples, calculated over the interval [:f:var:`start`, :f:var:`stop`].
      The start and end points of the interval can optionally be excluded.

      :p real start: Starting value of the sequence
      :p real stop: End value of the sequence
      :p integer num: Number of samples to generate
      :o logical istart: If :code:`.true.`, :f:var:`start` is included in the resulting array. Default :code:`.true.`
      :o logical iend: If :code:`.true.`, :f:var:`stop` is included in the resulting array. Default :code:`.true.`
      :o real mesh: If present, the step is saved in this variable
      :r real array(num): Contains :f:var:`num` equally spaced samples in the interval [:f:var:`start`, :f:var:`stop`], left/right open or closed depending on :f:var:`istart` and :f:var:`iend`

Points worth noting:

* the **signature** ``linspace(start, stop, num[, istart, iend, mesh])`` is
  built from the declarations: the arguments that have the ``optional``
  attribute are enclosed in square brackets. Nothing has to be written in the
  comment;
* the fields are ``:p`` (required argument), ``:o`` (optional argument) and
  ``:r`` (result of the function, that is the variable named after
  ``result(...)`` or the function itself), followed by the type, the shape
  (``array(num)``) and, when they exist, the attributes in brackets
  (``[in]``, ``[inout]``, ...);
* within the description, the name of an argument written with
  ``:f:var:`name``` becomes a link to that argument.

Ways to describe an argument
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Form
     - Where
     - Behaviour

   * - Inline comment
     - ``real(8) :: x  ! Description`` on the declaration line
     - **Recommended.** Wins over the other two forms.

   * - ``@param``
     - ``!@param x: description`` in the description block
     - The line is removed from the description and its text is
       *appended* to the inline description of ``x``, if any.

   * - Header line
     - ``!x: description`` in the description block
     - Copied to the description of ``x`` **and kept** in the text
       of the routine. Used only when there is no inline comment.

Example mixing the three forms:

.. code-block:: fortran

   subroutine axpy(a, x, y)
   !Computes :math:`y \leftarrow a x + y`.
   !
   !@param a: scalar factor
   !
   !y: header form (the line is also kept in the text!)
     real(8), intent(in)    :: a
     real(8), intent(in)    :: x(:)
     real(8), intent(inout) :: y(:)  !Vector updated in place
     y = a*x + y
   end subroutine axpy

.. code-block:: rst

   .. f:subroutine:: axpy(a, x, y)

      Computes :math:`y \leftarrow a x + y`.

      y: header form (the line is also kept in the text!)

      :p real a [in]:  scalar factor
      :p real x(:) [in]:
      :p real y(:) [inout]: Vector updated in place

.. warning::

   A header line **starting with the name of an argument** followed by a
   space or punctuation is read as the description of that argument, even
   if it was meant as ordinary prose: a sentence like ``x is scaled in place``
   would become the description of ``x`` (and would also stay in the text).
   Start sentences with another word. The positional form ``$1``, ``$2``,
   ... that appears in the source of the parser does not currently match
   (see :doc:`limitations`); do not rely on it.

.. _how-to-comment-limits:

Continuation lines
~~~~~~~~~~~~~~~~~~

A description may continue on the comment lines that follow the declaration.
Two details matter:

* consecutive lines are joined **without any separator**, so the previous line
  must end with a space, or the continuation must start with one;
* a bare ``!`` (nothing after it) closes the description. That is why the
  input variables of ``ED_INPUT_VARS`` are each followed by an empty ``!``.

.. code-block:: fortran

   integer :: bad   !First line
   !second line, no leading space
   integer :: good  !First line
   ! second line, with a leading space

.. code-block:: rst

   :f:var:`bad`, :f:var:`good`

   .. f:variable:: bad

      First linesecond line, no leading space

      :Type: integer

   .. f:variable:: good

      First line second line, with a leading space

      :Type: integer

Call relationships
~~~~~~~~~~~~~~~~~~

The ``:calledfrom:`` and ``:callto:`` fields (aliases ``:from:`` and
``:to:``) are ordinary fields of the description block and are shown as
*Called from* / *Call to* lists:

.. code-block:: fortran

   subroutine solve(a, b, x)
   !Solves the linear system.
   !
   !:calledfrom: main
   !:callto: factorize
   ...

They are **written by hand**. The parser also builds the lists of callers
and callees on its own (attributes ``callto`` and ``callfrom`` of each routine,
see :meth:`~sphinxfortran_ng.fortran_autodoc.F90toRst.build_callfrom_index`)
but does not print them.

Where the description block must be
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The block must be the very first thing after the signature (which may itself
span several lines with ``&``). If a ``use`` or ``implicit none`` comes first,
the description is silently lost:

.. code-block:: fortran

   subroutine s1(x)
     use iso_fortran_env
   !Described after a use statement: LOST
     real(8) :: x  !An x
   end subroutine s1

   subroutine s2(x)
   !Described right after the signature: kept
     use iso_fortran_env
     real(8) :: x  !An x
   end subroutine s2

.. code-block:: rst

   .. f:subroutine:: s1(x)

      :p real x: An x
      :use: :f:mod:`iso_fortran_env`

   .. f:subroutine:: s2(x)

      Described right after the signature: kept

      :p real x: An x
      :use: :f:mod:`iso_fortran_env`

Module Variables
----------------

Two styles are available and can be mixed.

**Same-line style**, for short descriptions:

.. code-block:: fortran

   real(8) :: pi  !Circle constant

**Trailing-bang style**, used by ``ED_INPUT_VARS``. The declaration line ends
with an empty ``!`` and the description follows on the next comment lines,
until a bare ``!`` (or any non-comment line) ends it:

.. code-block:: fortran

   real(8) :: beta    !
   !Inverse temperature.
   ! :Default beta:`1000d0`
   !
   integer :: nloop   !
   !Maximum number of loops. Uses a list:
   ! * :code:`0` : none
   ! * :code:`1` : all
   ! :Default nloop:`100`
   !
   integer :: forgotten
   !This comment is NOT attached (declaration has no trailing bang)

.. code-block:: rst

   :f:var:`beta`, :f:var:`nloop`, :f:var:`forgotten`

   .. f:variable:: beta

      Inverse temperature.

      :Type: real

      :Default: 1000d0

   .. f:variable:: forgotten

      :Type: integer

   .. f:variable:: nloop

      Maximum number of loops. Uses a list:

       * :code:`0` : none

       * :code:`1` : all

      :Type: integer

      :Default: 100

The rules that this example illustrates:

* the trailing ``!`` on the declaration line is mandatory in this style: it is
  what tells the parser that a description follows. ``forgotten`` gets none;
* a line of the form ``:Label varname:`value``` is removed from the text and
  shown as a ``:Label:`` field of the variable. This is how ``:Default:`` is
  produced in ``ED_INPUT_VARS``, but any label works (``:Units x:`eV```).
  **Only the first such line of a variable is kept**; further ones are
  dropped;
* lines starting with ``*`` are surrounded with blank lines, so bullet lists
  work. Other lines of a variable description are joined into a single line
  (see :ref:`continuation <how-to-comment-limits>` above), which means that
  literal blocks or multi-paragraph text cannot be written there;
* the type is printed with its **shape appended**: ``:Type: real(5)`` for
  ``real(c_double), dimension(5) :: Uloc`` is a real array of 5 elements, not
  ``kind=5``. The kind of a numeric type is not shown, the length of a
  ``character`` is;
* attributes (``save``, ``parameter``, ``public``, ...) appear in ``:Attributes:``
  and a ``bind(c, name="...")`` becomes the ``:Bindings:`` field; the initial
  value of the declaration, if any, becomes ``:Default:`` --- so do **not**
  also write ``:Default x:`` for a variable that has an initialiser, or
  it will be printed twice.
* Module variables are listed in **alphabetical order**, routines and types
  in source order.

Here are real variables from ``ED_INPUT_VARS``:

.. code-block:: fortran

   integer(c_int),bind(c, name="Nbath")       :: Nbath    !
   !Number of bath sites:
   ! * :f:var:`bath_type` = :code:`normal` : number of bath sites per orbital
   ! * :f:var:`bath_type` = :code:`hybrid` : total number of bath sites
   ! * :f:var:`bath_type` = :code:`replica/general` : number of replicas
   ! :Default Nbath:`6`
   !

.. code-block:: rst

   .. f:variable:: nbath

      Number of bath sites:

       * :f:var:`bath_type` = :code:`normal` : number of bath sites per orbital

       * :f:var:`bath_type` = :code:`hybrid` : total number of bath sites

       * :f:var:`bath_type` = :code:`replica/general` : number of replicas

      :Type: integer

      :Bindings: Language = **c**, Name = **nbath**
      :Default: 6

Derived Types
-------------

Derived types are documented like modules of variables: a description block
under the ``type`` line, then one inline comment per component.

.. code-block:: fortran

   type point
   !A point in the plane.
     real(8) :: x  !Abscissa
     real(8) :: y  !Ordinate
   end type point

.. code-block:: rst

   .. rubric:: Types

   .. f:type:: point

      A point in the plane.

      :f real x: Abscissa
      :f real y: Ordinate

.. warning::

   Only the plain form ``type name`` gets a description and component
   descriptions. With ``type :: name``, ``type, public :: name`` or
   ``type, extends(base) :: name`` the type is still listed, but without any
   description:

   .. code-block:: rst

      .. rubric:: Types

      .. f:type:: point

         :f real x:
         :f real y:

   Prefer ``type name``, and control the visibility with a separate
   ``public :: name`` statement placed **after** the type definition (see
   :ref:`visibility <how-to-comment-visibility>`).


Interfaces
----------

For a generic interface, put the description right under the ``interface``
line. The arguments are collected from all the procedures listed after
``module procedure``: when the implementations differ, the types are joined
(``integer,real``) and differing shapes are displayed as ``(various shapes)``.
The individual procedures are documented as usual.

.. code-block:: fortran

   interface twice
   !Generic interface: doubles an integer or a real.
     module procedure twice_i, twice_r
   end interface twice

.. code-block:: rst

   .. f:interface:: twice(x)

      Generic interface: doubles an integer or a real.

      :p integer,real x: Input
      :r integer,real y: Twice the input


Programs
--------

A main program is documented like a routine (description block under the
``program`` line) and is rendered with ``f:program``. Its ``use`` statements
are printed in a ``:use:`` field.

.. code-block:: fortran

   program main
   !Main program description
     use mymodule
   end program main


.. _how-to-comment-visibility:

Visibility (``public`` / ``private``)
-------------------------------------

Only public entities are documented. The parser follows the ``private`` and
``public`` statements and attributes of the module:

.. code-block:: fortran

   module m
     implicit none
     private
     public :: shown
     real(8) :: shown   !Public through the public statement
     real(8) :: secret  !Private by default
   end module m

.. code-block:: rst

   :f:var:`shown`

   .. f:variable:: shown

      Public through the public statement

      :Type: real

      :Attributes: public

Two things to know:

* for a **derived type** in a module made private by a bare ``private``
  statement, the ``public :: name`` statement must come **after** the type
  definition. Placed before, the type is hidden;
* the options ``:members:``, ``:undoc-members:`` and ``:forceadd-members:`` of
  ``f:automodule`` change the selection (see :doc:`fortran_autodoc`).


Using reStructuredText in comments
----------------------------------

All the usual constructs can be used in descriptions:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - You write in the comment
     - Result
   * - ``:code:`.true.```
     - inline literal, as in ``If :code:`.true.`, ...``
   * - ``:math:`N_{\uparrow}```
     - inline LaTeX maths
   * - ``:f:var:`num```, ``:f:func:`upmspace```, ``:f:mod:`sf_iotools```
     - links to variables, routines and modules of the Fortran domain
   * - ``* item`` on consecutive lines
     - bullet list (blank lines are added around each item)
   * - ``.. note::``, ``.. warning::``
     - admonition. In a **variable** description, put it after the bullets;
       its lines are joined into one, which is fine for a paragraph
   * - ``:calledfrom: name``
     - field of a routine description

Common indentation is removed, so the comment may be indented as the code is.
In descriptions of modules, routines and types the line structure is kept
(a bare ``!`` is a blank line), so these blocks accept any reST, including
literal blocks and several paragraphs.


Checklist: why is my description missing?
-----------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 33 33

   * - Symptom
     - Cause
     - Fix
   * - Routine or module has no description
     - Comment written before the signature, or after a ``use`` /
       ``implicit none``
     - Move it to the lines right after the signature
   * - Output contains ``>`` or ``!`` characters
     - ``!>`` / ``!!`` Doxygen markers
     - Use plain ``!``
   * - Module variable has no description (``g_ph_diag`` in
       ``ED_INPUT_VARS``)
     - Description on the next lines but the declaration has no trailing ``!``
     - Add the trailing ``!``
   * - Description of a variable is cut
     - A bare ``!`` in the middle of it
     - Use ``!`` followed by text, or restructure
   * - Two words glued together
     - Continuation line without leading space
     - Start the continuation with a space
   * - Type without description or components
     - ``type :: name`` or ``type, attr :: name``
     - Use ``type name``
   * - Type or variable missing
     - ``private`` by default
     - ``public :: name`` (after the type), or the ``public`` attribute
   * - ``:Default:`` shown twice
     - Initialiser in the declaration **and** ``:Default x:`` in the comment
     - Keep only one
   * - Helper variables such as ``ed_twin_`` appear
     - They are public and undocumented
     - Make them ``private`` or exclude them (see ``:undoc-members:``)
   * - Cross-reference not linked
     - Target not documented in this project, or wrong case
     - Document it or use the exact lower-case name

Summary
-------

If a Fortran entity (module, variable, function, type) has a properly
formatted comment block using reStructuredText, **inside** the entity for
modules, routines and types, and **at the end of the declaration** for
variables, it will be correctly parsed and indexed by Sphinx.
