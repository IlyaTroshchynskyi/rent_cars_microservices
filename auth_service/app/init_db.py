from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from app.config import get_settings
from app.db import init_dynamodb_resource


def create_table(ddb: DynamoDBServiceResource, table_name: str):
    settings = get_settings()
    ddb.create_table(
        TableName=table_name,
        AttributeDefinitions=[
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'user_name', 'AttributeType': 'S'},
        ],
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        ProvisionedThroughput={
            'ReadCapacityUnits': settings.READ_CAPACITY_UNITS,
            'WriteCapacityUnits': settings.WRITE_CAPACITY_UNITS
        },
        GlobalSecondaryIndexes=[
            {
                'IndexName': settings.USER_NAME_INDEX,
                'KeySchema': [{'AttributeName': 'user_name', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': settings.READ_CAPACITY_UNITS,
                    'WriteCapacityUnits': settings.WRITE_CAPACITY_UNITS
                }
            },
        ],
    )


if __name__ == '__main__':
    ddb = init_dynamodb_resource()
    create_table(ddb, 'users')
