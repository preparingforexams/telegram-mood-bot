resource aws_dynamodb_table "keyvalue" {
  name         = var.bot_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "key"
  attribute {
    name = "key"
    type = "S"
  }
  #   attribute {
  #     name = "value"
  #     type = "S"
  #   }
}

data "aws_iam_policy_document" "access_dynamodb" {
  statement {
    actions = [
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
      "dynamodb:GetItem",
      "dynamodb:UpdateItem"
    ]
    resources = [
      aws_dynamodb_table.keyvalue.arn
    ]
  }
}

resource "aws_iam_role_policy" "access_dynamodb" {
  name_prefix = var.bot_name
  role        = aws_iam_role.lambda_role.id

  policy = data.aws_iam_policy_document.access_dynamodb.json
}
