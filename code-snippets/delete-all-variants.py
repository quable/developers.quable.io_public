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
parser = argparse.ArgumentParser(description='Remove all variants from a given instance')
parser.add_argument('--instance', type=str, help='SubDomain of your QuablePIM', required=True)
parser.add_argument('--token', type=str, help='Access Token with full permissions', required=True)
args = parser.parse_args()

# Validating inputs
try:
    validate_instance(args.instance)
    validate_token(args.token)
except ValueError as e:
    logging.error(e)
    sys.exit(1)

# Initializing variables
variantCodes = []  # List to store variant IDs
urlGet = "https://{}.quable.com/api/variants?limit=25"  # URL for retrieving variants
urlDelete = "https://{}.quable.com/api_1.php/variants/{}"  # URL for deleting variants
headers = {
    'Authorization': 'Bearer {}'.format(args.token)  # Authorization header with access token
}

# Retrieving all variants
logging.info("Retrieve ALL variants - {}".format(urlGet.format(args.instance)))
try:
    response = requests.get(urlGet.format(args.instance), headers=headers)
    response.raise_for_status()
    response_dict = response.json()
except requests.RequestException as e:
    logging.error(f"Error retrieving variants: {e}")
    sys.exit(1)

# Loop to retrieve variants in chunks
for variant in response_dict.get("hydra:member", []):
    variantCodes.append(variant["id"])

while "hydra:view" in response_dict and "hydra:next" in response_dict["hydra:view"]:
    urlNext = "https://{}.quable.com{}".format(args.instance, response_dict["hydra:view"]["hydra:next"])
    logging.info("Retrieve ALL variants - {}".format(urlNext))
    try:
        response = requests.get(urlNext, headers=headers)
        response.raise_for_status()
        response_dict = response.json()
        for variant in response_dict.get("hydra:member", []):
            variantCodes.append(variant["id"])
    except requests.RequestException as e:
        logging.error(f"Error retrieving variants: {e}")
        sys.exit(1)

# Deleting variants one by one
logging.info("Delete variants one by one")
for variantCode in variantCodes:
    logging.info(f"Delete item: '{variantCode}'")
    try:
        response = requests.delete(urlDelete.format(args.instance, variantCode), headers=headers)
        if response.status_code == 204:
            logging.info(f"Variant '{variantCode}' deleted successfully.")
        else:
            logging.error(f"Failed to delete variant '{variantCode}'. Response: {response.text}")
    except requests.RequestException as e:
        logging.error(f"An error occurred while trying to delete variant '{variantCode}': {e}")

logging.info('END')
