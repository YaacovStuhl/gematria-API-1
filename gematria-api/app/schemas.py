from __future__ import annotations

from marshmallow import Schema, fields, validate


class GematriaQueryArgsSchema(Schema):
    phrase = fields.String(required=True, allow_none=False)


class GematriaLookupResponseSchema(Schema):
    phrase = fields.String(required=True)
    value = fields.Integer(required=True)
    found = fields.Boolean(required=True)


class MatchesQueryArgsSchema(Schema):
    value = fields.Integer(required=True)
    top = fields.Integer(load_default=10, validate=validate.Range(min=1, max=1000))


class EntrySchema(Schema):
    id = fields.Integer(required=True)
    phrase = fields.String(required=True)
    value = fields.Integer(required=True)
    source = fields.String(allow_none=True)


class EntryCreateSchema(Schema):
    phrase = fields.String(required=True)
    value = fields.Integer(required=True)
    source = fields.String(load_default=None, allow_none=True)


class EntryUpsertByPhraseSchema(Schema):
    phrase = fields.String(required=True)
    value = fields.Integer(required=True)
    source = fields.String(load_default=None, allow_none=True)


class BulkUpsertResponseSchema(Schema):
    requested = fields.Integer(required=True)
    unique = fields.Integer(required=True)
    upserted = fields.Integer(required=True)


class EntryUpdateSchema(Schema):
    phrase = fields.String(load_default=None, allow_none=True)
    value = fields.Integer(load_default=None, allow_none=True)
    source = fields.String(load_default=None, allow_none=True)


