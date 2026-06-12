from marshmallow import Schema, fields, validate, EXCLUDE


class FingerprintSubmitSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    participant_name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=255),
        error_messages={"required": "participant_name is required."},
    )

    fingerprint_result = fields.Dict(
        required=True,
        error_messages={"required": "fingerprint_result is required."},
    )