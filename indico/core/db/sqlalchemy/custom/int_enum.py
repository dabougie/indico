# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
from sqlalchemy import type_coerce
from sqlalchemy.sql.schema import CheckConstraint
from sqlalchemy.sql.sqltypes import SchemaType, SmallInteger
from sqlalchemy.sql.type_api import TypeDecorator


class _EnumIntWrapper(int):
    """Int subclass that keeps the repr of the enum's member."""

    def __init__(self, enum_member):
        self.enum_member = enum_member
        super(_EnumIntWrapper, self).__init__(enum_member.value)

    def __repr__(self):
        return repr(self.enum_member)


class PyIntEnum(TypeDecorator, SchemaType):
    """Custom type which handles values from a PEP-435 Enum.

    In addition to the Python-side validation this also creates a
    CHECK constraint to ensure only valid enum members are stored.

    :param enum: the Enum repesented by this type's values
    :raise ValueError: when using/loading a value not in the Enum.
    """

    impl = SmallInteger

    def __init__(self, enum=None):
        self.enum = enum
        TypeDecorator.__init__(self)
        SchemaType.__init__(self)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, self.enum):
            # Convert plain (int) value to enum member
            value = self.enum(value)
        return _EnumIntWrapper(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # Note: This raises a ValueError if `value` is not in the Enum.
        return self.enum(value)

    def _set_table(self, column, table):
        e = CheckConstraint(type_coerce(column, self).in_(x.value for x in self.enum))
        assert e.table is table

    def alembic_render_type(self, autogen_context):
        imports = autogen_context['imports']
        imports.add('from indico.core.db.sqlalchemy import PyIntEnum')
        imports.add('from {} import {}'.format(self.enum.__module__, self.enum.__name__))
        return '{}({})'.format(type(self).__name__, self.enum.__name__)