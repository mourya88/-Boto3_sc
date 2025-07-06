parameters = stack['Stacks'][0].get('Parameters', [])
print(f"Raw Parameters from CFN DescribeStacks: {parameters}")

if not parameters:
    print("❗No parameters found in CFN stack — check if they were defined in template.")
