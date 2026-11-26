# ---------------------------------------------------------------
# Amazon S3（VPC 内からは S3 Gateway Endpoint 経由でアクセスする）
# ---------------------------------------------------------------

resource "aws_s3_bucket" "app" {
  bucket_prefix = "${var.name_prefix}-app-"
}

resource "aws_s3_bucket_public_access_block" "app" {
  bucket = aws_s3_bucket.app.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
