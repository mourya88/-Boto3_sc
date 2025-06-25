# Get launch path required to describe provisioning parameters
launch_paths = sc_client.list_launch_paths(ProductId=product_id)
if not launch_paths['LaunchPathSummaries']:
    raise Exception(f"No Launch Paths found for Product ID: {product_id}")
path_id = launch_paths['LaunchPathSummaries'][0]['Id']

# Now call describe_provisioning_parameters with PathId
describe_outputs = sc_client.describe_provisioning_parameters(
    ProductId=product_id,
    ProvisioningArtifactId=artifact_id,
    PathId=path_id
)
