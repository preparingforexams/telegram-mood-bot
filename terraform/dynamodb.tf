resource aws_dynamodb_table "keyvalue" {
  name         = var.bot_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "key"
  attribute {
    name = "key"
    type = "S"
  }
}

resource aws_dynamodb_table "results" {
  name         = "${var.bot_name}-results"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "poll_id"
  range_key    = "user_id"

  attribute {
    name = "poll_id"
    type = "S"
  }
  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "time"
    type = "N"
  }

  local_secondary_index {
    name            = "time"
    range_key       = "time"
    projection_type = "ALL"
  }
}

resource aws_dynamodb_table "results2" {
  name         = "${var.bot_name}-results2"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "poll_id"
  range_key    = "user_id"

  attribute {
    name = "group_id"
    type = "S"
  }
  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "poll_id"
    type = "S"
  }
  attribute {
    name = "time"
    type = "N"
  }

  global_secondary_index {
    name            = "grouped"
    hash_key        = "group_id"
    range_key       = "time"
    projection_type = "ALL"
  }
}

resource aws_dynamodb_table "users" {
  name         = "${var.bot_name}-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  attribute {
    name = "user_id"
    type = "S"
  }
}

resource aws_dynamodb_table "groups" {
  name         = "${var.bot_name}-groups"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "group_id"
  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "group_id"
    type = "S"
  }
}

resource aws_dynamodb_table "api_users" {
  name         = "${var.bot_name}-api-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "refresh_token"
  attribute {
    name = "refresh_token"
    type = "S"
  }
}

resource aws_dynamodb_table "api_users_tg" {
  name         = "${var.bot_name}-api-user-tg"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  attribute {
    name = "user_id"
    type = "S"
  }
}

data "aws_iam_policy_document" "access_dynamodb" {
  statement {
    actions = [
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
      "dynamodb:GetItem",
      "dynamodb:UpdateItem",
      "dynamodb:Scan",
      "dynamodb:Query"
    ]
    resources = [
      aws_dynamodb_table.keyvalue.arn,
      aws_dynamodb_table.results.arn,
      aws_dynamodb_table.results2.arn,
      "${aws_dynamodb_table.results2.arn}/index/*",
      aws_dynamodb_table.users.arn,
      aws_dynamodb_table.groups.arn,
      aws_dynamodb_table.api_users.arn,
      aws_dynamodb_table.api_users_tg.arn
    ]
  }
}

resource "aws_iam_role_policy" "access_dynamodb" {
  name_prefix = var.bot_name
  role        = aws_iam_role.lambda_role.id

  policy = data.aws_iam_policy_document.access_dynamodb.json
}
