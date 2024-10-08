# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.


def get_policy_template(dataset_code: str) -> str:
    """Create policy template for admin user."""
    template = f'''
    {{
        "Version": "2012-10-17",
        "Statement": [
            {{
                "Action": [
                    "s3:ListBucket",
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:GetBucketLocation",
                    "s3:DeleteObject"],
                "Effect": "Allow",
                "Resource": ["arn:aws:s3:::{dataset_code}/*"]
            }}
        ]
    }}
    '''
    return template
