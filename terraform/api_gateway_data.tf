resource "aws_api_gateway_resource" "data" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "data"
}

resource "aws_api_gateway_resource" "data_me" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.data.id
  path_part   = "me"
}
