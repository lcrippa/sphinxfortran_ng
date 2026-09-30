# -*- coding: utf-8 -*-
"""A Fortran domain for Sphinx.

It provides the ``f`` domain: directives (``f:module``, ``f:function``, ...),
roles (``f:func``, ``f:var``, ...), a module index, and the doc fields used to
describe arguments, options, type fields and results.
"""
# Copyright or © or Copr. Actimar/IFREMER (2010-2019)
#
# This software is a computer program whose purpose is to provide
# utilities for handling oceanographic and atmospheric data,
# with the ultimate goal of validating the MARS model from IFREMER.
#
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.
#
import re
from collections import OrderedDict

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, Index, ObjType
from sphinx.locale import _
from sphinx.roles import XRefRole
from sphinx.util.docfields import DocFieldTransformer, Field, GroupedField, _is_single_paragraph
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_refnode

#: Separator between the module and the object names in targets
f_sep = '/'

#: Object types of intersphinx inventories that hold Fortran objects
_F_TYPES = ('f:module', 'f:subroutine', 'f:function', 'f:variable', 'f:type', 'f:interface')


# Utilities ---

def convert_arithm(node, expr, modname=None, nodefmt=nodes.Text):
    """Append an arithmetic expression to *node*, identifiers being cross-referenced as variables.

    :param node: Node to extend.
    :param expr: Expression, like ``"nx*2"``.
    :param modname: Module used to resolve the references.
    :param nodefmt: Node class used for text.
    """
    ops = re.findall(r'(\W+)', expr)
    nums = re.split(r'\W+', expr)
    if len(nums) != len(ops):
        ops.append('')
    for num, op in zip(nums, ops):
        if num:
            if num[0].isalpha():
                refnode = addnodes.pending_xref(
                    '', refdomain='f', reftype='var', reftarget=num, modname=modname)
                refnode += nodefmt(num, num)
                node += refnode
            else:
                node += nodefmt(num, num)
        if op:
            op = op.replace(':', '•')
            node += nodefmt(op, op)


def parse_shape(shape):
    """Enclose *shape* in parentheses if needed. Return ``None`` if it is empty."""
    if not shape:
        return
    if not shape.startswith('('):
        shape = '(' + shape
    if not shape.endswith(')'):
        shape += ')'
    return shape


def add_shape(node, shape, modname=None, nodefmt=nodes.Text):
    """Append a shape expression, like ``"(nx, ny)"``, to *node*."""
    node += nodefmt(' (', ' (')
    convert_arithm(node, shape[1:-1], modname=modname, nodefmt=nodefmt)
    node += nodefmt(')', ')')


def _preferred_crossrefs(env):
    """Get the ``preferred-crossrefs`` of the current document (``{}`` if none)."""
    return getattr(env, 'preferred_crossrefs', {}).get(env.docname, {})


def FortranCreateIndexEntry(indextext, fullname, modname):
    """Create an index entry (see https://github.com/sphinx-doc/sphinx/issues/2673)."""
    return ('single', indextext, fullname, modname, None)


# Doc fields ---

#: Splits a field name into ``type``, ``n`` (name), ``shape`` and ``sattrs``
re_fieldname_match = re.compile(
    r'(?P<type>(?:\b\w+\b(?:\(.*\))?,?)+)?\s*(?P<n>\b\w+\b)\s*(?P<shape>\(.*\))?\s*(?P<sattrs>\[.+\])?').match


class FortranField(Field):
    """Doc field whose cross-references carry the current module and type."""

    def make_xref(self, rolename, domain, target, innernode=nodes.emphasis,
                  modname=None, typename=None):
        """Create a cross-reference node, or a plain *innernode* if there is no *rolename*."""
        if not rolename:
            return innernode(target, target)
        refnode = addnodes.pending_xref(
            '', refdomain=domain, refexplicit=False, reftype=rolename,
            reftarget=target, modname=modname, typename=typename)
        refnode += innernode(target, target)
        return refnode


class FortranCallField(FortranField):
    """Grouped doc field listing calls (``calledfrom`` and ``callto``) on one line."""
    is_grouped = True

    def __init__(self, name, names=(), label=None, rolename=None):
        Field.__init__(self, name, names, label, True, rolename)

    def make_field(self, types, domain, items, **kwargs):
        """Create a field whose body is the space-joined contents of *items*."""
        fieldname = nodes.field_name('', self.label)
        par = nodes.paragraph()
        for i, item in enumerate(items):
            if i:
                par += nodes.Text(' ')
            par += item[1]
        return nodes.field('', fieldname, nodes.field_body('', par))


class FortranCompleteField(FortranField, GroupedField):
    """Grouped doc field with type, shape and attributes for each argument.

    The type, shape and attributes are given either with the argument, or with
    separate fields whose names are in *typenames*, *shapenames* and *attrnames*::

        :param type name(shape) [attr1,attr2]: description
        :param name: description
        :type name: type
    """
    is_typed = 2

    def __init__(self, name, names=(), typenames=(), label=None,
                 rolename=None, typerolename=None,
                 shapenames=None, attrnames=None,
                 prefix=None, strong=True, can_collapse=False):
        GroupedField.__init__(self, name, names, label, rolename, can_collapse)
        self.typenames = typenames
        self.typerolename = typerolename
        self.shapenames = shapenames
        self.attrnames = attrnames
        self.prefix = prefix
        self.namefmt = nodes.strong if strong else addnodes.desc_name

    def make_field(self, types, domain, items, shapes=None, attrs=None,
                   modname=None, typename=None):
        """Create the field from *items*, popping the types, shapes and attributes of the arguments."""

        def handle_item(fieldarg, content):
            par = nodes.paragraph()
            if self.prefix:
                par += self.namefmt(self.prefix, self.prefix)
            par += self.make_xref(self.rolename, domain, fieldarg, self.namefmt,
                                  modname=modname, typename=typename)

            fieldtype = types.pop(fieldarg, None)
            fieldshape = shapes and shapes.pop(fieldarg, None)
            fieldattrs = attrs and attrs.pop(fieldarg, None)
            if fieldshape:
                add_shape(par, parse_shape(fieldshape[0].astext()), modname=modname)
            if fieldtype or fieldattrs:
                par += nodes.emphasis(' [', ' [')
            if fieldtype:
                if len(fieldtype) == 1 and isinstance(fieldtype[0], nodes.Text):
                    for i, thistypename in enumerate(fieldtype[0].astext().split(',')):
                        if i:
                            par += nodes.emphasis(', ', ', ')
                        par += self.make_xref(self.typerolename, domain, thistypename,
                                              modname=modname, typename=typename)
                else:
                    par += fieldtype
            if fieldattrs:
                if fieldtype:
                    par += nodes.emphasis(', ', ', ')
                par += fieldattrs
            if fieldtype or fieldattrs:
                par += nodes.emphasis(']', ']')
            if content:
                par += nodes.Text(' -- ')
                par += content
            return par

        if len(items) == 1 and self.can_collapse:
            fieldarg, content = items[0]
            bodynode = handle_item(fieldarg, content)
        else:
            bodynode = self.list_type()
            for fieldarg, content in items:
                bodynode += nodes.list_item('', handle_item(fieldarg, content))
        fieldname = nodes.field_name('', self.label or '')
        return nodes.field('', fieldname, nodes.field_body('', bodynode))


class FortranDocFieldTransformer(DocFieldTransformer):
    """Transform field lists into doc fields, handling types, shapes and attributes.

    :param directive: Directive owning the doc field types.
    :param modname: Current module name.
    :param typename: Current type name.
    """

    def __init__(self, directive, modname=None, typename=None):
        self.domain = directive.domain
        if '_doc_field_type_map' not in directive.__class__.__dict__:
            directive.__class__._doc_field_type_map = \
                self.preprocess_fieldtypes(directive.__class__.doc_field_types)
        self.typemap = directive._doc_field_type_map
        self.modname = modname
        self.typename = typename

    def preprocess_fieldtypes(self, types):
        """Map each field name to ``(fieldtype, kind)`` with kind in
        ``False``, ``'types'``, ``'shapes'`` or ``'attrs'``."""
        typemap = OrderedDict()
        for fieldtype in types:
            for name in fieldtype.names:
                typemap[name] = fieldtype, False
            if fieldtype.is_typed:
                for kind, names in (('types', fieldtype.typenames),
                                    ('shapes', fieldtype.shapenames),
                                    ('attrs', fieldtype.attrnames)):
                    for name in names:
                        typemap[name] = fieldtype, kind
        return typemap

    def scan_fieldarg(self, fieldname):
        """Extract name, shape, type and attributes from a field argument.

        Syntaxes: ``name``, ``type name``, ``type name(shape) [attr1,attr2]``
        or ``name [attr1, attr2]``.

        :return: ``name, shape, type, attributes``. Missing items are ``None``.
            Several types (interfaces) are joined with ``/`` instead of ``,``.
        """
        if fieldname[0] == ',':
            fieldname = fieldname[1:]
        m = re_fieldname_match(fieldname.strip())
        if not m:
            raise ValueError(
                'Wrong field (%s). It must have at least one parameter name and one argument' %
                fieldname)
        ftype, name, shape, attrs = m.groups()
        if ftype is not None:
            ftype = ftype.replace(',', '/')
        attrs = attrs and attrs[1:-1]
        return name, shape, ftype, attrs

    def transform(self, node):
        """Transform a single field list *node*."""
        typemap = self.typemap
        entries = []
        groupindices = OrderedDict()
        types = OrderedDict()
        shapes = OrderedDict()
        attrs = OrderedDict()
        collections = {'types': types, 'shapes': shapes, 'attrs': attrs}

        # Step 1: collect field types and contents
        for field in node:
            fieldname, fieldbody = field
            try:
                fieldtype, fieldarg = fieldname.astext().split(None, 1)
            except ValueError:  # argument-less field
                fieldtype, fieldarg = fieldname.astext(), ''
            typedesc, is_typefield = typemap.get(fieldtype, (None, None))

            # Unknown field: capitalize its name and pass it through
            if typedesc is None:
                fieldname[0] = nodes.Text(fieldtype.capitalize() + ' ' + fieldarg)
                entries.append(field)
                continue

            typename = typedesc.name

            # Content, without unnecessary paragraphs
            if _is_single_paragraph(fieldbody):
                content = fieldbody.children[0].children
            else:
                content = fieldbody.children

            # Field giving the type, shape or attributes of an argument
            if is_typefield:
                # only inline nodes, else the markup is invalid
                content = [n for n in content if isinstance(n, (nodes.Inline, nodes.Text))]
                if content:
                    collections[is_typefield].setdefault(typename, OrderedDict())[fieldarg] = content
                continue

            # Syntax ``:param type name(shape) [attrs]:`` or ``:param type name:``
            if typedesc.is_typed == 2:
                argname, argshape, argtype, argattrs = self.scan_fieldarg(fieldarg)
                if argtype:
                    types.setdefault(typename, OrderedDict())[argname] = [nodes.Text(argtype)]
                if argshape:
                    shapes.setdefault(typename, OrderedDict())[argname] = [nodes.Text(argshape)]
                if argattrs:
                    attrs.setdefault(typename, OrderedDict())[argname] = \
                        [nodes.emphasis(argattrs, argattrs)]
                fieldarg = argname
            elif typedesc.is_typed:
                try:
                    argtype, argname = fieldarg.split(None, 1)
                except ValueError:
                    pass
                else:
                    types.setdefault(typename, OrderedDict())[argname] = [nodes.Text(argtype)]
                    fieldarg = argname

            # Grouped entries share one entry, the others have one entry per field
            if typedesc.is_grouped:
                if typename in groupindices:
                    group = entries[groupindices[typename]]
                else:
                    groupindices[typename] = len(entries)
                    group = [typedesc, []]
                    entries.append(group)
                group[1].append(typedesc.make_entry(fieldarg, content))
            else:
                entries.append([typedesc, typedesc.make_entry(fieldarg, content)])

        # Step 2: build the new field list
        new_list = nodes.field_list()
        for entry in entries:
            if isinstance(entry, nodes.field):  # unknown field
                new_list += entry
                continue
            fieldtype, content = entry
            new_list += fieldtype.make_field(
                types.get(fieldtype.name, OrderedDict()), self.domain, content,
                shapes=shapes.get(fieldtype.name, OrderedDict()),
                attrs=attrs.get(fieldtype.name, OrderedDict()),
                modname=self.modname, typename=self.typename)
        node.replace_self(new_list)


# Signatures ---

#: Fortran signature: type, objtype, module, type name, name, arguments
f_sig_re = re.compile(
    r'''^ (\w+(?:[^%%%(f_sep)s]%(f_sep)s\w+))? \s*          # type
          (\b(?:subroutine|function|interface))?  \s*             # objtype
          (\b\w+%(f_sep)s)?              # module name
          (\b\w+%%)?              # type name
          (\b\w+|operator\([^\)]+\)|assignment\(=\))  \s*             # thing name
          (?: \(([^\(\)]*)\))?           # optional: arguments
           $                   # and nothing more
          ''' % dict(f_sep=f_sep), re.VERBOSE + re.I)


def _pseudo_parse_arglist(signode, arglist):
    """Add to *signode* a parameter list from arguments separated by commas.

    Optional arguments are enclosed in brackets. If the brackets are unbalanced,
    the whole list is used as a single argument.
    """
    paramlist = addnodes.desc_parameterlist()
    stack = [paramlist]
    try:
        for argument in arglist.split(','):
            argument = argument.strip()
            ends_open = ends_close = 0
            while argument.startswith('['):
                stack.append(addnodes.desc_optional())
                stack[-2] += stack[-1]
                argument = argument[1:].strip()
            while argument.startswith(']'):
                stack.pop()
                argument = argument[1:].strip()
            while argument.endswith(']'):
                ends_close += 1
                argument = argument[:-1].strip()
            while argument.endswith('['):
                ends_open += 1
                argument = argument[:-1].strip()
            if argument:
                stack[-1] += addnodes.desc_parameter(argument, argument)
            while ends_open:
                stack.append(addnodes.desc_optional())
                stack[-2] += stack[-1]
                ends_open -= 1
            while ends_close:
                stack.pop()
                ends_close -= 1
        if len(stack) != 1:
            raise IndexError
    except IndexError:
        signode += addnodes.desc_parameterlist()
        signode[-1] += addnodes.desc_parameter(arglist, arglist)
    else:
        signode += paramlist


# Directives ---

#: Text of the object type in the index entries
_INDEX_OBJTYPE = {
    'type': 'fortran type',
    'variable': 'fortran variable',
    'subroutine': 'fortran subroutine',
    'function': 'fortran function',
    'interface': 'fortran interface',
    'module': 'fortran module',
    'program': 'fortran program',
}


class FortranObject(ObjectDescription):
    """Description of a general Fortran object (used as is for variables)."""
    option_spec = {
        'noindex': directives.flag,
        'module': directives.unchanged,
        'type': directives.unchanged,
        'shape': parse_shape,
        'attrs': directives.unchanged,
    }

    doc_field_types = [
        FortranCompleteField('parameter', label=_('Parameters'),
                             names=('p', 'param', 'parameter', 'a', 'arg', 'argument'),
                             typerolename='type',
                             typenames=('paramtype', 'type', 'ptype'),
                             shapenames=('shape', 'pshape'),
                             attrnames=('attrs', 'pattrs', 'attr'),
                             can_collapse=True),
        FortranCompleteField('optional', label=_('Options'),
                             names=('o', 'optional', 'opt', 'keyword', 'option'),
                             typerolename='type',
                             typenames=('optparamtype', 'otype'),
                             shapenames=('oshape',),
                             attrnames=('oattrs', 'oattr'),
                             can_collapse=True),
        FortranCompleteField('typefield', label=_('Type fields'),
                             names=('f', 'field', 'typef', 'typefield'),
                             typerolename='type',
                             typenames=('fieldtype', 'ftype'),
                             shapenames=('fshape',),
                             attrnames=('fattrs', 'fattr'),
                             prefix='',
                             strong=False,
                             can_collapse=False),
        FortranCompleteField('return', label=_('Result'),
                             names=('r', 'return', 'returns'),
                             typerolename='type',
                             typenames=('returntype', 'rtype'),
                             shapenames=('rshape',),
                             attrnames=('rattrs', 'rattr'),
                             can_collapse=True),
        FortranCallField('calledfrom', label=_('Called from'), names=('calledfrom', 'from')),
        FortranCallField('callto', label=_('Call to'), names=('callto', 'to')),
    ]

    #: Suffix of the name in the index entries
    _parens = ''

    def get_signature_prefix(self, sig):
        """Get the prefix to put before the object name in the signature."""
        return ''

    def needs_arglist(self):
        """Tell if an argument list is displayed even if the signature has none."""
        return False

    def handle_signature(self, sig, signode):
        """Transform a Fortran signature into nodes.

        :return: ``fullname, type``, where *fullname* is ``module/name``
            (``_`` if there is no module), or just ``name`` for a program.
        :raises ValueError: If the signature cannot be parsed.
        """
        m = f_sig_re.match(sig)
        if m is None:
            raise ValueError
        ftype, objtype, modname, typename, name, arglist = m.groups()
        typename = typename or ''

        # Module, type, shape and attributes
        modname = (modname and modname[:-1]) or self.options.get(
            'module', self.env.temp_data.get('f:module'))
        if typename:
            name = typename[:-1]
        attrs = self.options.get('attrs')
        shape = parse_shape(self.options.get('shape'))
        ftype = ftype or self.options.get('type')

        if self.objtype == 'program':
            fullname = name
        else:
            fullname = (modname or '_') + f_sep + name
        signode['module'] = modname
        signode['type'] = typename
        signode['fullname'] = fullname

        # "function" or "subroutine" tag, module and name
        sig_prefix = self.get_signature_prefix(sig)
        if objtype or sig_prefix:
            objtype = objtype or sig_prefix
            signode += addnodes.desc_annotation(objtype + ' ', objtype + ' ')
        if self.env.config.add_module_names and modname:
            nodetext = modname + f_sep
            signode += addnodes.desc_addname(nodetext, nodetext)
        signode += addnodes.desc_name(name, name)

        # Arguments of callables, else shape of variables
        if self.needs_arglist():
            if arglist:
                _pseudo_parse_arglist(signode, arglist)
            else:
                signode += addnodes.desc_parameterlist()
        elif arglist and not shape:
            shape = arglist

        self.add_shape_and_attrs(signode, modname, ftype, shape, attrs)
        return fullname, ftype

    def add_shape_and_attrs(self, signode, modname, ftype, shape, attrs):
        """Add the shape, the type and the attributes (``[type,attr1,default=1]``) to *signode*."""
        if shape:
            add_shape(signode, shape, modname=modname)
        if ftype or attrs:
            signode += nodes.emphasis(' [', ' [')
        if ftype:
            refnode = addnodes.pending_xref(
                '', refdomain='f', reftype='type', reftarget=ftype, modname=modname)
            refnode += nodes.emphasis(ftype, ftype)
            signode += refnode
        if attrs:
            if ftype:
                signode += nodes.emphasis(',', ',')
            for iatt, att in enumerate(re.split(r'\s*,\s*', attrs)):
                if iatt:
                    signode += nodes.emphasis(',', ',')
                if att.startswith('default'):
                    signode += nodes.emphasis('default=', 'default=')
                    convert_arithm(signode, att.split('=')[1], modname=modname)
                else:
                    signode += nodes.emphasis(att, att)
        if ftype or attrs:
            signode += nodes.emphasis(']', ']')

    def add_target_and_index(self, name, sig, signode):
        """Register the object in the domain, and add its index entry."""
        modname = signode.get('module', self.env.temp_data.get('f:module'))
        fullname = 'f' + f_sep + name[0]

        if fullname not in self.state.document.ids:
            signode['names'].append(fullname)
            signode['ids'].append(fullname)
            signode['first'] = (not self.names)
            self.state.document.note_explicit_target(signode)
            objects = self.env.domaindata['f']['objects']
            if fullname in objects:
                print(self.env.docname,
                      'duplicate object description of ', fullname,
                      'other instance in ',
                      self.env.doc2path(objects[fullname][0]),
                      self.lineno)
            objects[fullname] = (self.env.docname, self.objtype)
        indextext = self.get_index_text(modname, fullname)
        if indextext:
            self.indexnode['entries'].append(FortranCreateIndexEntry(indextext, fullname, fullname))

    def before_content(self):
        """Reset the flag telling if the current type is set by this object."""
        self.typename_set = False

    def after_content(self):
        """Unset the current type if it was set by this object."""
        if self.typename_set:
            self.env.temp_data['f:type'] = None

    def get_index_text(self, modname, name):
        """Get the text of the index entry, like ``"name() (fortran function in module mod)"``."""
        if name.startswith('f' + f_sep):
            name = name[len('f' + f_sep):]
        mn = modname or '_'
        if name.startswith(mn + f_sep):
            name = name[len(mn) + 1:]
        sobj = _INDEX_OBJTYPE.get(self.objtype)
        sobj = _(sobj) if sobj else ''
        if self.objtype in ('module', 'program'):
            modname = ''
        sinmodule = (_(' in module %s') % modname) if modname and self.env.config.add_module_names else ''
        return '%s%s (%s%s)' % (name, self._parens, sobj, sinmodule)


class FortranSpecial(object):
    """Mixin displaying the object type (``subroutine``, ...) before the name."""

    def get_signature_prefix(self, sig):
        """Get the object type as prefix."""
        return self.objtype + ' '


class WithFortranDocFieldTransformer(object):
    """Mixin running :class:`FortranDocFieldTransformer` on the content of the directive."""

    def run(self):
        """Same as :meth:`sphinx.directives.ObjectDescription.run`
        but using :class:`FortranDocFieldTransformer`."""
        if ':' in self.name:
            self.domain, self.objtype = self.name.split(':', 1)
        else:
            self.domain, self.objtype = '', self.name
        if not hasattr(self, 'env'):
            self.env = self.state.document.settings.env
        self.indexnode = addnodes.index(entries=[])

        node = addnodes.desc()
        node.document = self.state.document
        node['domain'] = self.domain
        node['objtype'] = node['desctype'] = self.objtype  # 'desctype' is kept for compatibility
        node['noindex'] = noindex = ('noindex' in self.options)

        # One signature node and one target for each signature
        self.names = []
        for sig in self.get_signatures():
            signode = addnodes.desc_signature(sig, '')
            signode['first'] = False
            node.append(signode)
            try:
                name = self.handle_signature(sig, signode)
            except ValueError:  # parsing failed: no index entry
                signode.clear()
                signode += addnodes.desc_name(sig, sig)
                continue
            if not isinstance(name[0], str):
                name = (str(name), name[1])
            # only the first description of an object of this block is indexed
            if not noindex and name not in self.names:
                self.names.append(name)
                self.add_target_and_index(name, sig, signode)

        # Module and type of the last signature
        modname = signode.get('module')
        typename = signode.get('type')
        contentnode = addnodes.desc_content()
        node.append(contentnode)
        if self.names:  # for version{added,changed} directives
            self.env.temp_data['object'] = self.names[0]
        self.before_content()
        self.state.nested_parse(self.content, self.content_offset, contentnode)
        FortranDocFieldTransformer(self, modname=modname, typename=typename).transform_all(contentnode)
        self.env.temp_data['object'] = None
        self.after_content()
        return [self.indexnode, node]


class FortranType(FortranSpecial, WithFortranDocFieldTransformer, FortranObject):
    """Directive ``f:type``. The type is the current one while its content is parsed."""

    def before_content(self):
        """Set the current type to the described one."""
        FortranObject.before_content(self)
        if self.names:
            self.env.temp_data['f:type'] = self.names[0][0].split(f_sep)[-1]
            self.typename_set = True


class FortranProgram(FortranSpecial, WithFortranDocFieldTransformer, FortranObject):
    """Directive ``f:program``."""


class FortranWithSig(FortranSpecial, WithFortranDocFieldTransformer, FortranObject):
    """Directive ``f:function``, ``f:subroutine`` and ``f:interface``: objects with arguments."""
    _parens = '()'

    def needs_arglist(self):
        """Always display the argument list."""
        return True


class FortranModule(Directive):
    """Directive ``f:module``: mark the description of a new module and make it current."""
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'platform': lambda x: x,
        'synopsis': lambda x: x,
        'noindex': directives.flag,
        'deprecated': directives.flag,
    }

    def run(self):
        """Register the module in the domain, set it as current, and add its target and index entry."""
        env = self.state.document.settings.env
        modname = self.arguments[0].strip()
        env.temp_data['f:module'] = modname
        env.domaindata['f']['modules'][modname] = (
            env.docname, self.options.get('synopsis', ''),
            self.options.get('platform', ''), 'deprecated' in self.options)
        env.domaindata['f']['objects']['f' + f_sep + modname] = (env.docname, 'module')
        targetnode = nodes.target('', '', ids=['f' + f_sep + modname], ismod=True)
        self.state.document.note_explicit_target(targetnode)
        ret = [targetnode]
        if 'platform' in self.options:  # the synopsis is only used in the module index
            platform = self.options['platform']
            node = nodes.paragraph()
            node += nodes.emphasis('', _('Platforms: '))
            node += nodes.Text(platform, platform)
            ret.append(node)
        if 'noindex' not in self.options:
            indextext = _('%s (module)') % modname
            ret.append(addnodes.index(
                entries=[FortranCreateIndexEntry(indextext, 'f' + f_sep + modname, modname)]))
        return ret


class FortranCurrentModule(Directive):
    """Directive ``f:currentmodule``: document objects of a module without a link to it.

    .. note:: The current module is always reset to ``None``, whatever the argument
        (the original conditions led to that in both cases).
    """
    has_content = False
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = False
    option_spec = OrderedDict()

    def run(self):
        """Reset the current module."""
        self.state.document.settings.env.temp_data['f:module'] = None
        return []


class FortranXRefRole(XRefRole):
    """Role for cross-references to Fortran objects, with intersphinx fallback."""

    @staticmethod
    def _is_local(env, targetshort):
        """Tell if an object of the domain has the (lower case) short name *targetshort*."""
        return any(targetshort == key.lower().split(f_sep)[-1]
                   for key in env.domaindata['f']['objects'])

    @staticmethod
    def _find_intersphinx(env, target, targetshort):
        """Get the full name of *target* from the intersphinx inventories.

        :raises Exception: If the inventories are not available or *target* is not found.
        """
        all_invs = env.intersphinx_named_inventory
        which_invs = [inv for inv in all_invs if any(t in all_invs[inv] for t in _F_TYPES)]
        targetlist = []
        for inv in which_invs:
            for jkey in all_invs[inv]:
                for ikey in all_invs[inv][jkey]:
                    if (targetshort == ikey.split(f_sep)[-1].lower()
                            and ikey.lower().startswith('f' + f_sep)
                            and (targetlist == [] or (ikey not in targetlist[-1]
                                                      and targetlist[-1] not in ikey))):
                        targetlist.append(ikey)

        preferred = _preferred_crossrefs(env)
        if target in preferred and preferred[target] in targetlist:
            targetlist = [preferred[target]]
        if len(targetlist) > 1:
            print("Warning, duplicate labels for " + target + ": ", targetlist)
        return targetlist[0]

    def process_link(self, env, refnode, has_explicit_title, title, target):
        """Store the current module and type in *refnode*, and normalize the title and target.

        A leading ``.`` of the title and a leading ``~`` of the target are
        ignored. If the target is not in the domain, it is searched in the
        intersphinx inventories. A leading ``~`` in the title hides the
        module part, and a leading separator in the target searches the more
        specific namespaces first.
        """
        refnode['f:module'] = env.temp_data.get('f:module')
        refnode['f:type'] = env.temp_data.get('f:type')
        if not has_explicit_title:
            title = title.lstrip('.')
            target = target.lstrip('~').lower()
            targetshort = target.split(f_sep)[-1]
            if not self._is_local(env, targetshort):
                try:
                    target = self._find_intersphinx(env, target, targetshort)
                except Exception:
                    pass
            if title[0:1] == '~':
                title = title[1:].split(f_sep, 1)[-1]
        if target.startswith(f_sep):
            target = target[1:]
            refnode['refspecific'] = True
        return title, target


class FortranModuleIndex(Index):
    """Fortran module index."""
    name = 'modindex'
    localname = _('Fortran Module Index')
    shortname = _('fortran modules')

    def generate(self, docnames=None):
        """Get the index content, sorted by first letter, and the collapse flag."""
        content = OrderedDict()
        ignores = sorted(self.domain.env.config['modindex_common_prefix'], key=len, reverse=True)
        modules = sorted(self.domain.data['modules'].items(), key=lambda x: x[0].lower())
        prev_modname = ''
        num_toplevels = 0
        for modname, (docname, synopsis, platforms, deprecated) in modules:
            if docnames and docname not in docnames:
                continue

            for ignore in ignores:
                if modname.startswith(ignore):
                    modname = modname[len(ignore):]
                    stripped = ignore
                    break
            else:
                stripped = ''
            if not modname:  # the whole name was stripped
                modname, stripped = stripped, ''

            entries = content.setdefault(modname[0].lower(), [])
            package = modname.split(f_sep)[0]
            if package != modname:  # submodule
                if prev_modname == package:  # first submodule: the parent becomes a group head
                    entries[-1][1] = 1
                elif not prev_modname.startswith(package):  # no parent in the list: dummy entry
                    entries.append([stripped + package, 1, '', '', '', '', ''])
                subtype = 2
            else:
                num_toplevels += 1
                subtype = 0

            qualifier = _('Deprecated') if deprecated else ''
            entries.append([stripped + modname, subtype, docname,
                            'f' + f_sep + stripped + modname, platforms,
                            qualifier, synopsis or ''])
            prev_modname = modname

        # Collapse only if there are more toplevel modules than submodules
        collapse = len(modules) - num_toplevels < num_toplevels
        return sorted(content.items()), collapse


class FortranDomain(Domain):
    """Fortran language domain (``f``).

    Data: ``objects`` maps ``f/module/name`` to ``(docname, objtype)`` and
    ``modules`` maps a module name to ``(docname, synopsis, platform, deprecated)``.
    """
    name = 'f'
    label = 'Fortran'
    object_types = {
        'program': ObjType(_('program'), 'prog'),
        'type': ObjType(_('type'), 'type'),
        'variable': ObjType(_('variable'), 'var'),
        'function': ObjType(_('function'), 'func', 'func_inline'),
        'subroutine': ObjType(_('subroutine'), 'func', 'func_inline', 'subr', 'subr_inline'),
        'interface': ObjType(_('interface'), 'func', 'func_inline', 'subr', 'subr_inline'),
        'module': ObjType(_('module'), 'mod'),
    }
    directives = {
        'program': FortranProgram,
        'type': FortranType,
        'variable': FortranObject,
        'function': FortranWithSig,
        'subroutine': FortranWithSig,
        'interface': FortranWithSig,
        'module': FortranModule,
        'currentmodule': FortranCurrentModule,
    }
    roles = {
        'prog': FortranXRefRole(),
        'type': FortranXRefRole(),
        'var': FortranXRefRole(),
        'func': FortranXRefRole(fix_parens=True),
        'func_inline': FortranXRefRole(fix_parens=False),
        'subr': FortranXRefRole(fix_parens=True),
        'subr_inline': FortranXRefRole(fix_parens=False),
        'mod': FortranXRefRole(),
    }
    initial_data = {
        'objects': OrderedDict(),  # fullname -> docname, objtype
        'modules': OrderedDict(),  # modname -> docname, synopsis, platform, deprecated
    }
    indices = [FortranModuleIndex]

    def clear_doc(self, docname):
        """Remove the objects and modules of document *docname*."""
        for fullname, (fn, _objtype) in list(self.data['objects'].items()):
            if fn == docname:
                del self.data['objects'][fullname]
        for modname, (fn, _s, _p, _d) in list(self.data['modules'].items()):
            if fn == docname:
                del self.data['modules'][modname]

    def find_obj(self, env, modname, name, role, searchorder=0):
        """Find the objects matching *name*, perhaps using the module *modname*.

        :param role: Role of the reference, that restricts the object types.
        :param searchorder: ``1`` for relative search (``:role:`/name```): the
            object types are checked and the module is tried first. Else, an
            exact match is looked for, regardless of the type.
        :return: List of ``(fullname, (docname, objtype))``, empty if there is
            no match. Falls back on a search of the short name among all
            objects of a compatible type.
        """
        if name.endswith('()'):
            name = name[:-2]
        if not name:
            return None, None
        if f_sep in name and any(c.isalnum() for c in name.split(f_sep)[-1]):
            modname, name = name.split(f_sep, 1)
        if '%' in name:
            name, _tmp = name.split('%')

        objects = self.data['objects']
        objtypes = self.objtypes_for_role(role)
        ismod = role in ('mod', 'prog')

        def key(*parts):
            return f_sep.join(('f',) + parts)

        if searchorder == 1:  # :role:`/toto`
            if ismod:
                if key(name) not in objects:  # exact match only
                    return []
                newname = key(name)
            else:
                candidates = [key(modname, name)] if modname else []
                candidates += [key('_', name), key(name), name]
                newname = next((c for c in candidates
                                if c in objects and objects[c][1] in objtypes), None)
        else:  # :role:`toto`, the object type is not considered
            if key(name) in objects:
                newname = key(name)
            elif ismod:  # exact match only
                return []
            else:
                candidates = [key('_', name)] + ([key(modname, name)] if modname else [])
                newname = next((c for c in candidates if c in objects), None)

        if newname is not None:
            return [(newname, objects[newname])]
        # Last chance: fuzzy search
        nameshort = name.split(f_sep)[-1]
        return [(oname, objects[oname]) for oname in objects
                if oname.endswith(f_sep + nameshort) and objects[oname][1] in objtypes]

    def resolve_xref(self, env, fromdocname, builder, type, target, node, contnode):
        """Resolve a cross-reference, taking into account the ``preferred-crossrefs`` of the document."""
        modname = node.get('f:module', node.get('modname'))
        searchorder = int(node.hasattr('refspecific'))
        matches = self.find_obj(env, modname, target, type, searchorder)

        preferred = _preferred_crossrefs(env)
        if target in preferred:
            target = preferred[target]
            matches = [(target, self.data['objects'][target])]

        if not matches:
            return None
        if len(matches) > 1:
            print(fromdocname,
                  'more than one target found for cross-reference '
                  '%r: %s' % (target, ', '.join(match[0] for match in matches)),
                  node.line)
        name, obj = matches[0]

        if obj[1] == 'module':  # additional info of modules
            docname, synopsis, platform, deprecated = self.data['modules'][name[1 + len(f_sep):]]
            assert docname == obj[0]
            title = name
            if synopsis:
                title += ': ' + synopsis
            if deprecated:
                title += _(' (deprecated)')
            return make_refnode(builder, fromdocname, docname, name, contnode, title)
        return make_refnode(builder, fromdocname, obj[0], name, contnode, name)

    def get_objects(self):
        """Yield the modules, then the other objects, for the search index."""
        for modname, info in self.data['modules'].items():
            yield (modname, modname, 'module', info[0], 'module-' + modname, 0)
        for refname, (docname, type) in self.data['objects'].items():
            yield (refname, refname, type, docname, refname, 1)


class PreferredCrossrefsDirective(SphinxDirective):
    """Directive ``preferred-crossrefs``: choose, for the current document, the target of ambiguous references.

    Each line of the content is ``name: full/target``.
    """
    has_content = True

    def run(self):
        """Store the choices in ``env.preferred_crossrefs[docname]``."""
        crossrefs = {}
        for line in self.content:
            line = line.strip()
            if not line:
                continue
            if line.startswith(':'):
                line = line[1:].lstrip()
            parts = line.split(':', 1)
            if len(parts) != 2:  # exactly one colon is needed
                continue
            crossrefs[parts[0].strip()] = parts[1].strip()

        env = self.env
        if not hasattr(env, 'preferred_crossrefs'):
            env.preferred_crossrefs = {}
        env.preferred_crossrefs.setdefault(env.docname, {}).update(crossrefs)
        return []


def setup(app):
    """Sphinx entry point: register the ``preferred-crossrefs`` directive and the Fortran domain."""
    app.add_directive('preferred-crossrefs', PreferredCrossrefsDirective)
    app.add_domain(FortranDomain)
