Fortran Domain
==============

The Fortran domain provided by ``sphinxfortran_ng`` defines a set of
directives and roles for documenting Fortran entities explicitly.

Unlike the autodoc directives, which extract documentation directly from
source files, the Fortran domain directives are written manually and give
full control over structure, formatting, and content.

The domain name for all directives and roles is ``f``. Activate it with:

.. code-block:: python

   extensions += ["sphinxfortran_ng.fortran_domain"]

.. contents:: On this page
   :local:
   :depth: 2


Overview
--------

The Fortran domain supports documentation of:

- programs
- modules
- subroutines
- functions
- generic interfaces
- variables
- derived types

Each entity can be documented using a dedicated directive, and entities
can be cross-referenced using domain-specific roles. The ``f:auto*`` directives
of :doc:`fortran_autodoc` do nothing else than generating this text.

.. list-table::
   :header-rows: 1
   :widths: 22 30 48

   * - Directive
     - Role(s)
     - Notes
   * - ``f:module``
     - ``:f:mod:``
     - Sets the current module. No content.
   * - ``f:currentmodule``
     - --
     - Resets the current module.
   * - ``f:program``
     - ``:f:prog:``
     - Main program.
   * - ``f:subroutine``
     - ``:f:func:``, ``:f:subr:``
     - Takes an argument list.
   * - ``f:function``
     - ``:f:func:``
     - Takes an argument list.
   * - ``f:interface``
     - ``:f:func:``, ``:f:subr:``
     - Takes an argument list.
   * - ``f:type``
     - ``:f:type:``
     - Derived type, components in ``:f`` fields.
   * - ``f:variable``
     - ``:f:var:``
     - Module variable, type component.
   * - ``preferred-crossrefs``
     - --
     - Not in the domain: disambiguates references (see
       :ref:`preferred-crossrefs`).


Module and Program Directives
------------------------------

``.. f:module::``
~~~~~~~~~~~~~~~~~

Declare a Fortran module. It records the module in the module index, creates
the target of the module and makes it the *current module* for the objects
that follow, until the next ``f:module`` or ``f:currentmodule``.

The directive takes **no content**: the description of the module is written
as normal paragraphs after it, not indented under it.

Syntax
^^^^^^

.. code-block:: rst

   .. f:module:: module_name
      :synopsis: Short description shown in the module index
      :platform: any
      :deprecated:
      :noindex:

   Description of the module, written as ordinary paragraphs.

Options
^^^^^^^

``:synopsis:``
   One line shown in the Fortran module index, and as the tooltip of the
   references to the module.

``:platform:``
   Platforms on which the module is available, printed as a line
   *Platforms: ...* under the declaration.

``:deprecated:``
   Flag the module as deprecated in the index and in the references.

``:noindex:``
   Do not add the module to the index.

``.. f:currentmodule::``
~~~~~~~~~~~~~~~~~~~~~~~~

Document objects **without linking them to a module**. It resets the current
module to nothing, whatever its optional argument. The objects that follow are
then registered as ``_/name`` and are found by their short name. The
``f:auto*`` directives use it for the objects they insert.

``.. f:program::``
~~~~~~~~~~~~~~~~~~

Declare and describe a Fortran program unit. It accepts the same content and
fields as a routine.

Syntax
^^^^^^

.. code-block:: rst

   .. f:program:: program_name

      Description of the program.

      :calledfrom: nothing


Routine Directives
------------------

``.. f:subroutine::``
~~~~~~~~~~~~~~~~~~~~~

Document a Fortran subroutine. The word ``subroutine`` is added in front of
the name in the signature automatically, and the module is shown in front of it
when the Sphinx option ``add_module_names`` is true.

Syntax
^^^^^^

.. code-block:: rst

   .. f:subroutine:: subroutine_name(arg1, arg2[, opt1, opt2])

      Description of the subroutine.

Optional arguments are enclosed in **square brackets**, exactly as in a
Python signature: the brackets open before the first optional argument and
close after the last one (``a[, b[, c]]`` nests them). The signature is
otherwise free text, with these exceptions:

* it can be prefixed by the module and a slash: ``.. f:subroutine:: sf_arrays/linspace(a, b)``;
* the words ``subroutine``, ``function`` or ``interface`` may also be
  written first;
* the arguments must be a flat list in **one** pair of parentheses.

.. warning::

   A trailing ``result(...)`` clause, or a type in front (``real function``),
   makes the signature unparsable: it is then displayed as a plain string and
   the object gets **no index entry and no cross-reference target**. Give the
   result in a ``:r`` field instead.

``.. f:function::``
~~~~~~~~~~~~~~~~~~~

Document a Fortran function. Same syntax as ``f:subroutine``; describe the
value with a ``:r`` field.

.. code-block:: rst

   .. f:function:: linspace(start, stop, num[, istart, iend, mesh])

      Returns an array of evenly spaced numbers over a specified interval.

      :p real start: Starting value of the sequence
      :p real stop: End value of the sequence
      :p integer num: Number of samples to generate
      :o logical istart: If :code:`.true.`, :f:var:`start` is included
      :o logical iend: If :code:`.true.`, :f:var:`stop` is included
      :o real mesh: If present, the step is saved in this variable
      :r real array(num): The :f:var:`num` samples

``.. f:interface::``
~~~~~~~~~~~~~~~~~~~~

Document a generic interface. Same syntax and fields as a function. Where the
specific procedures have different types, list them separated by commas:
``:p integer,real x: ...``.

Options common to all objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The directives of routines, types, programs and variables accept:

``:noindex:``
   Do not register the object nor add an index entry.

``:module:``
   Name of the module the object belongs to, when it differs from the current
   module.

``:type:``, ``:shape:``, ``:attrs:``
   Type, shape and attributes displayed in the signature of a **variable**
   (see below).


Argument and Variable Descriptions
----------------------------------

Subroutines, functions, interfaces, programs and derived types accept **field
lists** to describe arguments, components and results.

Each family of fields collects a *description* together with the *type*, the
*shape* and the *attributes* of a name. They can be given in the field name
itself:

.. code-block:: rst

   :p real(kind=dp) A(n,m) [in]: Coefficient matrix

or in separate fields (see the table below):

.. code-block:: rst

   :p A: Coefficient matrix
   :type A: real(kind=dp)
   :shape A: (n,m)
   :attrs A: in

Available fields
~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 14 24 20 20 22

   * - Title shown
     - Field names
     - Type
     - Shape
     - Attributes
   * - Parameters
     - ``p``, ``param``, ``parameter``, ``a``, ``arg``, ``argument``
     - ``type``, ``ptype``, ``paramtype``
     - ``shape``, ``pshape``
     - ``attrs``, ``attr``, ``pattrs``
   * - Options
     - ``o``, ``optional``, ``opt``, ``option``, ``keyword``
     - ``otype``, ``optparamtype``
     - ``oshape``
     - ``oattrs``, ``oattr``
   * - Type fields
     - ``f``, ``field``, ``typef``, ``typefield``
     - ``ftype``, ``fieldtype``
     - ``fshape``
     - ``fattrs``, ``fattr``
   * - Result
     - ``r``, ``return``, ``returns``
     - ``rtype``, ``returntype``
     - ``rshape``
     - ``rattrs``, ``rattr``
   * - Called from
     - ``calledfrom``, ``from``
     - --
     - --
     - --
   * - Call to
     - ``callto``, ``to``
     - --
     - --
     - --

In the generated documentation, ``:p`` is used for required arguments, ``:o``
for optional ones, ``:r`` for the result and ``:f`` for the components of a
type. Any other field, such as ``:use:`` or ``:Default:`` in the output of the
autodoc directives, is displayed as it is, with the first letter capitalised.

.. note::

   ``Parameters`` and ``Options`` are the arguments **of a routine** or a
   program. They have nothing to do with the Fortran ``parameter`` attribute.

Syntax of the field name
~~~~~~~~~~~~~~~~~~~~~~~~

The name of the ``:p``, ``:o``, ``:f`` and ``:r`` fields is analysed as::

   [type] name[(shape)] [[attr1,attr2]]

.. list-table::
   :header-rows: 1
   :widths: 46 54

   * - Field
     - Reading
   * - ``:p start:``
     - name only
   * - ``:p real start:``
     - type ``real``
   * - ``:p real array(num):``
     - type ``real``, shape ``(num)``. The names in a shape are links to the
       variables of the same name.
   * - ``:p integer p [in,required]:``
     - attributes ``in`` and ``required``
   * - ``:p character(len=*) name:``
     - type with a parenthesis, no space
   * - ``:p integer,real x:``
     - several types, for an interface
   * - ``:r real(kind=dp) y(n) [out]:``
     - result, with kind, shape and attribute

Keep the type, the shape and the attributes free of spaces and commas, except
the comma between the attributes of the brackets: forms such as
``:p real, dimension(:,:) A:`` or ``:p real x [intent(in), optional]:`` are
not analysed correctly. Put such a type in a separate field instead:
``:type A: real, dimension(:,:)``.

The name of the type is a link to the ``f:type`` of that name if there is one;
the intrinsic types are left as text.

The result field always needs a name. Write ``:r real y: Description``:
a bare ``:returns: Description`` is not accepted and stops the build with an
``IndexError``.

Call relationships
~~~~~~~~~~~~~~~~~~

``:calledfrom:`` and ``:callto:`` take a list of names, written as
references to routines, in the body of the field; each is displayed on a
single line.

.. code-block:: rst

   :calledfrom: :f:func:`upminterval`
   :callto: :f:func:`linspace`

Documenting a routine, fully
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: rst

   .. f:function:: upmspace(start, stop, p, u, ndim[, base, istart, iend, mesh])

      Returns an array of numbers spaced linearly between exponentially spaced
      checkpoints. The interval is first divided into :f:var:`p` coarse
      regions, each of which is then divided linearly into :f:var:`u`
      subintervals.

      :p real start: First element of the array
      :p real stop: Last element of the array
      :p integer p: Number of coarse subdivisions
      :p integer u: Number of fine subdivisions
      :p integer ndim: Length of the output array, :math:`p \cdot u` or :math:`p \cdot u + 1`
      :o real base: Base of the exponential spacing (default :code:`2`)
      :o logical istart: If :code:`.true.`, :f:var:`start` is included
      :o logical iend: If :code:`.true.`, :f:var:`stop` is included
      :o real mesh(ndim): Distances between consecutive points
      :r real aout(ndim): The generated points
      :calledfrom: :f:func:`upminterval`
      :callto: :f:func:`linspace`


Derived Types
-------------

``.. f:type::``
~~~~~~~~~~~~~~~

Document a Fortran derived type. While its content is parsed, the type is the
*current type*, which is used to resolve the references of its components.

Syntax
^^^^^^

.. code-block:: rst

   .. f:type:: matrix

      Derived type representing a dense matrix.

      :f integer nrow: Number of rows
      :f integer ncol: Number of columns
      :f real(kind=dp) data(nrow,ncol): Matrix storage array

The components are described with the fields ``:f`` (aliases ``field``,
``typef``, ``typefield``), with the same name syntax as an argument. Since
``nrow`` and ``ncol`` appear in a shape, they become links to the components
of that name.


Variables
---------

``.. f:variable::``
~~~~~~~~~~~~~~~~~~~

Document a module variable or a type component.

Syntax
^^^^^^

.. code-block:: rst

   .. f:variable:: beta
      :type: real
      :attrs: default=1000d0

      Inverse temperature, at zero temperature it is used as a IR cut-off.

.. code-block:: rst

   .. f:variable:: uloc(5)
      :type: real
      :attrs: bind

      Values of the local interaction per orbital.

Options
^^^^^^^

``:type:``
   Type of the variable, linked to the type of that name when there is one.

``:shape:``
   Shape, for instance ``(n, m)``. The parentheses are added if missing. The
   shape can also be written in the signature: ``uloc(5)``. Identifiers in it
   are links to variables.

``:attrs:``
   Comma separated attributes, displayed after the type. An attribute
   starting with ``default=`` shows its value, with the identifiers linked to
   the variables.

The signature is displayed as ``name (shape) [type,attrs]``.

The autodoc directives add the description fields ``:Type:``,
``:Attributes:``, ``:Bindings:`` and ``:Default:`` to the content of the
variables. They are ordinary fields and do not belong to the domain.


.. _domain-roles:

Cross-Referencing
-----------------

Fortran entities can be referenced using domain roles:

.. list-table::
   :header-rows: 1
   :widths: 30 34 36

   * - Role
     - Refers to
     - Displayed as
   * - ``:f:mod:`linalg```
     - module
     - ``linalg``
   * - ``:f:func:`solve```
     - function, subroutine or interface
     - ``solve()``
   * - ``:f:func_inline:`solve```
     - same as ``func``
     - ``solve`` (no parentheses)
   * - ``:f:subr:`solve```
     - subroutine or interface
     - ``solve()``
   * - ``:f:subr_inline:`solve```
     - same as ``subr``
     - ``solve`` (no parentheses)
   * - ``:f:type:`matrix```
     - derived type
     - ``matrix``
   * - ``:f:var:`beta```
     - variable, or type component
     - ``beta``
   * - ``:f:prog:`main```
     - program
     - ``main``

These roles create hyperlinks to the corresponding documented entities.

How a target is looked up
~~~~~~~~~~~~~~~~~~~~~~~~~

The lookup is case-insensitive. The target can be:

``name``
   The exact name, then ``name`` in no module, then in the current module,
   and finally any object of a compatible type whose name ends with the
   target.

``module/name``
   The name in that module, for instance ``:f:func:`sf_arrays/linspace```.

``~module/name``
   As above, but the title shows only ``name``.

``/name``
   A relative search: the current module comes first, and the type of the
   object must fit the role.

Explicit titles work as in the other domains:
``:f:func:`the linspace function <sf_arrays/linspace>```. References to a
module also show its synopsis as a tooltip.

When a name is not defined in the project but exists in an Intersphinx
inventory that holds Fortran objects, the link goes to that inventory.

.. _preferred-crossrefs:

Ambiguous references
~~~~~~~~~~~~~~~~~~~~

If several objects share a name (for instance a variable ``beta`` defined by
two modules), Sphinx uses the first one it finds and prints a message. The
``preferred-crossrefs`` directive chooses the target for the references of
**one document**. Each line of its content is ``name: complete/target``, where
the target is the full name of the object, ``module/name``:

.. code-block:: rst

   .. preferred-crossrefs::

      beta: ed_input_vars/beta
      linspace: sf_arrays/linspace

.. note::

   The directive is registered without a domain prefix, and it is not
   validated: a wrong target raises an error at the first reference to it.


Indices
-------

The domain contributes the *Fortran Module Index*, which lists the modules
declared by ``f:module`` (or ``f:automodule``) with their synopsis, platforms
and deprecation status. It is available through

.. code-block:: rst

   :ref:`f-modindex`

The modules, and the other objects, are also added to the general index and
to the search index. The text of the index entries is
``name() (fortran function)``, followed by ``in module <name>`` when
``add_module_names`` is true.


Formatting Guidelines
---------------------

To produce consistent and readable documentation:

- Use one ``:p`` field per argument, and ``:o`` for the optional ones
- Give the type of each argument in the field, so that it links to the type
  definition
- Keep field descriptions concise; use paragraphs above them for details
- Give the default value of an optional argument in its description
- Use inline literals (``:code:``) for Fortran symbols and expressions
- Do not write ``result(...)`` in a signature


When to Use the Fortran Domain
------------------------------

Manual Fortran domain directives are recommended when:

- Autodoc output needs customization
- Code cannot be parsed automatically
- Documentation must be written independently of source layout

Autodoc and manual directives may be freely mixed in the same project: for
instance ``f:automodule`` with ``:hide-output: 1`` declares the module, and the
routines are then written by hand or inserted one by one with
``f:autoroutine`` in the order of your choice.
