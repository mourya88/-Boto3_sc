def parameters_changed(existing_params, new_params):
    # Convert both lists to dictionaries using correct key names
    existing_dict = {p["ParameterKey"]: p.get("DefaultValue", "") for p in existing_params}
    new_dict = {p["Key"]: p["Value"] for p in new_params}

    print("Existing:", existing_dict)
    print("New:", new_dict)

    return existing_dict != new_dict
