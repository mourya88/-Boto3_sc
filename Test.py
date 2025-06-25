if provisioned:
    artifact_needs_update = (artifact_id != existing_artifact_id)

    # Step 1: Fetch product_id
    response = sc_client.search_products(Filters={"FullTextSearch": [product_name]})
    product_id = None
    for product_view in response['ProductViewSummaries']:
        if product_view['Name'] == product_name:
            product_id = product_view['ProductId']
            break
    if not product_id:
        raise Exception(f"Product with name {product_name} not found!")

    # Step 2: Get Launch Path
    launch_paths = sc_client.list_launch_paths(ProductId=product_id)
    if not launch_paths['LaunchPathSummaries']:
        raise Exception(f"No Launch Paths found for Product ID: {product_id}")
    path_id = launch_paths['LaunchPathSummaries'][0]['Id']

    # Step 3: Describe parameters
    describe_outputs = sc_client.describe_provisioning_parameters(
        ProductId=product_id,
        ProvisioningArtifactId=artifact_id,
        PathId=path_id
    )

    current_params = describe_outputs.get("ProvisioningArtifactParameters", [])
    params_need_update = parameters_changed(current_params, parameters)
