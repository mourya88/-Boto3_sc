if not parameters:
    print("❗ No parameters found in CFN stack – check if they were defined in template.")

# Convert CFN parameters to same format
current_params = [
    {"ParameterKey": p["ParameterKey"], "DefaultValue": p["ParameterValue"]}
    for p in parameters
]
print(f"🟢 Current Parameters (from CFN): {json.dumps(current_params, indent=2)}")

return current_params
