FORBIDDEN_MODEL_FIELDS = {
    "email",
    "internal_note",
    "id",
}

def validate_approved_fields(approved_fields):
    forbidden_fields = set(approved_fields) & FORBIDDEN_MODEL_FIELDS

    if forbidden_fields:
        field_list = ", ".join(sorted(forbidden_fields))
        raise ValueError(
            f"forbidden field requested for model use: {field_list}"
        )

def build_model_context(campaign, contact):
    approved_fields = campaign["approved_fields"]
    validate_approved_fields(approved_fields)

    return {
        "purpose": campaign["purpose"],
        "contact": {
            field: contact[field]
            for field in approved_fields
        },
    }

def build_data_minimisation_record(campaign, contact):
    approved_fields = campaign["approved_fields"]
    validate_approved_fields(approved_fields)

    return {
        "used_fields": list(approved_fields),
        "excluded_fields": sorted(
            field
            for field in contact
            if field not in approved_fields
        ),
    }
