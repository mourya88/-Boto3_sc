
import re

def get_current_parameters(provisioned_id, aws_creds):
    session = create_session(aws_creds)
    sc_client = session.client("servicecatalog")
    cfn_client = session.client("cloudformation")

    history = sc_client.list_record_history(
        AccessLevelFilter={'Key': 'Account', 'Value': 'self'},
        SearchFilter={'key': 'provisionedproduct', 'value': provisioned_id}
    )

    print("list_record_history output:")
    print(json.dumps(history, indent=4, default=str))

    record_details = history.get('RecordDetails', [])

    for record in record_details:
        if record.get('Status') == 'SUCCEEDED' and record.get('RecordType') in ['PROVISION_PRODUCT', 'UPDATE_PROVISIONED_PRODUCT']:
            record_id = record.get('RecordId')
            record_info = sc_client.describe_record(Id=record_id)
            print(f"record_info: {record_info}")

            # Extract stack ARN from RecordOutputs
            outputs = record_info['RecordDetail'].get('RecordOutputs', [])
            for output in outputs:
                if output['Key'] == 'CloudFormationStackARN':
                    stack_arn = output['Value']
                    print(f"Extracted CloudFormation Stack ARN: {stack_arn}")
                    # Extract stack name from ARN
                    stack_name = stack_arn.split("/")[-1]
                    print(f"Parsed Stack Name: {stack_name}")

                    # Get parameters from CloudFormation
                    stack = cfn_client.describe_stacks(StackName=stack_name)
                    parameters = stack['Stacks'][0].get('Parameters', [])
                    print("CFN Parameters:", parameters)

                    # Convert CFN parameters to same format
                    current_params = [{"ParameterKey": p["ParameterKey"], "DefaultValue": p["ParameterValue"]} for p in parameters]
                    print("Current Parameters (from CFN):", current_params)
                    return current_params

    print("No matching SUCCEEDED record found or parameters missing.")
    return []
