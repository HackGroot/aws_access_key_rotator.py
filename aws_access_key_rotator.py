import boto3
import datetime
import os
import argparse

# Specify the AWS region to use
region = 'us-west-2'

# Create an IAM client
iam_client = boto3.client('iam', region_name=region)

# Define a function to create a new access key for the specified IAM user
def create_access_key(iam_user_name):
    # Create a new access key for the specified IAM user
    response = iam_client.create_access_key(UserName=iam_user_name)
    new_access_key_id = response['AccessKey']['AccessKeyId']
    new_secret_access_key = response['AccessKey']['SecretAccessKey']
    print(f'Created new access key {new_access_key_id} for user {iam_user_name}.')

    # Set the new access key as the default for the user
    iam_client.update_access_key(
        UserName=iam_user_name,
        AccessKeyId=new_access_key_id,
        Status='Active'
    )

    # Store the new access key and secret access key in environment variables
    os.environ['AWS_ACCESS_KEY_ID'] = new_access_key_id
    os.environ['AWS_SECRET_ACCESS_KEY'] = new_secret_access_key

# Define a function to rotate the access key for the specified IAM user
def rotate_access_key(iam_user_name, threshold_age):
    # Get the current access key for the specified IAM user
    response = iam_client.list_access_keys(UserName=iam_user_name)
    current_access_key = response['AccessKeyMetadata'][0]
    current_access_key_id = current_access_key['AccessKeyId']
    current_access_key_age = (datetime.datetime.now(datetime.timezone.utc) -
                              current_access_key['CreateDate']).days
    print(f'Access key {current_access_key_id} for user {iam_user_name} is {current_access_key_age} days old.')

    # Create a new access key if the current access key is older than the threshold age
    if current_access_key_age >= threshold_age:
        create_access_key(iam_user_name)

        # Deactivate the old access key
        iam_client.update_access_key(
            UserName=iam_user_name,
            AccessKeyId=current_access_key_id,
            Status='Inactive'
        )
        print(f'Deactivated access key {current_access_key_id} for user {iam_user_name}.')
    else:
        print(f'Access key {current_access_key_id} for user {iam_user_name} is not due for rotation yet.')

# Main function
def main():
    # Parse the command line arguments
    parser = argparse.ArgumentParser(description='Automate the generation and rotation of AWS access keys and secret access keys for an IAM user.')
    parser.add_argument('iam_user_name', help='the name of the IAM user to manage')
    parser.add_argument('--threshold-age', type=int, default=90, help='the age threshold (in days) for rotating the access key (default: 90)')
    args = parser.parse_args()

    # Rotate the access key for the specified IAM user
    rotate_access_key(args.iam_user_name, args.threshold_age)

if __name__ == '__main__':
    main()
