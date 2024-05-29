# python3 ./delete-attributes.py  --instance=xxx --token=xxx --attributes=attr1,attr2

import argparse  # Library for parsing command-line arguments
import requests  # Library for making HTTP requests
import json      # Library for working with JSON data
import logging   # Library for logging messages
import sys       # Library for system-specific parameters and functions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def validate_token(token):
    if not token or len(token) < 20:  # Example condition, adjust as necessary
        raise ValueError("Invalid token. Token must be at least 20 characters long.")

def validate_instance(instance):
    if not instance or not instance.isalnum():
        raise ValueError("Invalid instance. Instance must be alphanumeric.")

# Parsing command-line arguments
parser = argparse.ArgumentParser(description='Remove given attributes from a given instance')
parser.add_argument('--instance', type=str, help='SubDomain of your QuablePIM', required=True)
parser.add_argument('--token', type=str, help='Access Token with full permissions', required=True)
parser.add_argument('--attributes', type=str, help='List of attribute codes (comma separated)', required=True)
args = parser.parse_args()

# Validating inputs
try:
    validate_instance(args.instance)
    validate_token(args.token)
except ValueError as e:
    logging.error(e)
    sys.exit(1)

# Initializing variables
attributeCodes = args.attributes.split(',')
urlApiAttributes = "https://{}.quable.com/api/attributes/{}"
headers = {
    'Authorization': 'Bearer {}'.format(args.token)  # Authorization header with access token
}

logging.info("Starting to delete attributes one by one")
for attributeCode in attributeCodes:
    url = urlApiAttributes.format(args.instance, attributeCode)
    logging.info(f"Deleting attribute '{attributeCode}' - {url}")
    try:
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            logging.info(f"Attribute '{attributeCode}' deleted successfully.")
        else:
            logging.error(f"Failed to delete attribute '{attributeCode}'. Response: {response.text}")
    except requests.RequestException as e:
        logging.error(f"An error occurred while trying to delete attribute '{attributeCode}': {e}")

logging.info('END')
