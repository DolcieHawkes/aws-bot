import boto3
import json
import secrets
import string
import os


REGION = os.environ['AWS_REGION']
ChatbotUserPool = os.getenv("Cognito_UserPool", None)
ChatbotUserPoolClient = os.getenv("Cognito_ClientID", None)
secrets_name = os.getenv("SECRET_ID", 'ui-credentials')
user_id = os.getenv("USER_ID", 'bedrock')


cognitoidentityserviceprovider = boto3.client('cognito-idp', region_name=REGION)

def generate_random_password(length=12):
    # Define character sets
    lowercase_letters = string.ascii_lowercase
    uppercase_letters = string.ascii_uppercase
    digits = string.digits
    special_characters = '!$@'

    # Ensure that the password includes at least one special character
    special_char = secrets.choice(special_characters)

    # Calculate the remaining length of the password
    remaining_length = length - 1

    # Generate the rest of the password with a mix of characters
    password_characters = (
        secrets.choice(lowercase_letters) +
        secrets.choice(uppercase_letters) +
        secrets.choice(digits) +
        ''.join(secrets.choice(lowercase_letters + uppercase_letters + digits + special_characters) for _ in range(remaining_length - 3))
    )

    # Shuffle the characters to make the password random
    password_list = list(password_characters)
    secrets.SystemRandom().shuffle(password_list)
    shuffled_password = ''.join(password_list)

    # Add the special character back at a random position
    position = secrets.randbelow(length)
    password = shuffled_password[:position] + special_char + shuffled_password[position:]

    return password

def create_secret(password):

    # Initialize the AWS Secrets Manager client
    client = boto3.client('secretsmanager')

    # Store the user ID and password in a dictionary
    secret_data = {
        'user_id': user_id,
        'password': password
    }

    # Create or update the secret in Secrets Manager
    try:
        response = client.create_secret(
            Name=secrets_name,
            SecretString=str(secret_data)
        )
        print("Secret created successfully!")
    except client.exceptions.ResourceExistsException:
        # If the secret already exists, update it
        response = client.update_secret(
            SecretId=secrets_name,
            SecretString=str(secret_data)
        )
        print("Secret updated successfully!")


def lambda_handler(event, context):
    status_msg = 'SUCCESS'
    try:
        password = generate_random_password()
        create_secret(password)
        
        try:
            cognitoidentityserviceprovider.admin_create_user(
                UserPoolId = ChatbotUserPool,
                Username = user_id, 
                UserAttributes = [
                    {"Name": "name", "Value": user_id}
                ]
            )
        except Exception as e1:
            print('cognito user exist already')

        cognitoidentityserviceprovider.admin_set_user_password(
            UserPoolId = ChatbotUserPool,
            Username = user_id, 
            Password = password,
            Permanent=True
        )
        status_msg = 'SUCCESS'
    except Exception as e:
        print('Error: ' + str(e))
        status_msg = 'FAILED'
        

    print('Successfully created user')


