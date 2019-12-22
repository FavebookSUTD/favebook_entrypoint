import boto3
from base64 import b64encode
from os import chmod
import time
from sys import argv

if len(argv) != 3:
    print(f"Expected 3 Arguments but got {len(argv)} instead")
    print("Correct usage: python3 databasesetupcloud.py <ACCESS KEY> and <SECRET KEY>")
    exit(1)


ACCESS_KEY = argv[1] # insert your access key
SECRET_KEY = argv[2]  # insert your AWS secret key here
STACK_NAME = 'AoogebraStack'

print(f"ACCESS KEY: {ACCESS_KEY}\n",
      f"SECRET_KEY: {SECRET_KEY}")

def createkeypair():
	ec2client = boto3.client('ec2', 'ap-southeast-1', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY);
	all_pairs = ec2client.describe_key_pairs()['KeyPairs']

	if all_pairs == []:
		priv = ec2client.create_key_pair(KeyName='DBKeyPair')
		with open('DBKeyPair.pem', 'w') as file:
			file.write(priv['KeyMaterial'])
		chmod('DBKeyPair.pem', 0o400)
		priv_pem64 = b64encode(priv['KeyMaterial'].encode())
		print("Created Hadoop key pair.")
		return priv_pem64

	if not any(pair['KeyName'] == 'DBKeyPair' for pair in all_pairs):
	    print("Key pair does not exist. Creating.")
	    priv = ec2client.create_key_pair(KeyName='DBKeyPair')
	    with open('DBKeyPair.pem', 'w') as file:
	        file.write(priv['KeyMaterial'])
	    chmod('DBKeyPair.pem', 0o400)
	    priv_pem64 = b64encode(priv['KeyMaterial'].encode())
	    print("Created Hadoop key pair.")
	else:
	    print("Hadoop key pair exists.")
	    with open('DBKeyPair.pem', 'rb') as file:
	        filebytes = file.read()
	        priv_pem64 = b64encode(filebytes)
	return priv_pem64

def deletestack(client):
	client.delete_stack(StackName=STACK_NAME)

def createstack(client, priv_pem64):
	client.create_stack(StackName=STACK_NAME, TemplateURL='https://aoogebradatabasesetup.s3-ap-southeast-1.amazonaws.com/stacksetup.json', 
		Parameters=[{'ParameterKey':'KeyPair', 'ParameterValue': 'DBKeyPair'}, {'ParameterKey':'PrivKey', 'ParameterValue': priv_pem64.decode()}])


# Main function
client = boto3.client('cloudformation', 'ap-southeast-1', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

priv_pem64 = createkeypair()
createstack(client, priv_pem64)

waiter = client.get_waiter('stack_create_complete')

waiter.wait(
    StackName='AoogebraStack',
    WaiterConfig={
        'Delay': 30,
        'MaxAttempts': 123
    }
)

exports = {exportdict['Name']: exportdict['Value'] for exportdict in client.list_exports()['Exports']}
print('Flask Backend IP: {}:5000/docs/'.format(exports['FlaskPublicIP']))
print('Frontend Public IP: {}:3000'.format(exports['FrontendPublicIP']))
print('Frontend Admin Public IP: {}:3001'.format(exports['FrontendAdminPublicIP']))
print('Spark Public IP: {}'.format(exports['NamenodePublicIP']))





