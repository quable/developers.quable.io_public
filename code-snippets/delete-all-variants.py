# Importing necessary libraries
import argparse  # Library for parsing command-line arguments
import requests  # Library for making HTTP requests
import json      # Library for working with JSON data

# Parsing command-line arguments
parser = argparse.ArgumentParser(description='Remove all variants from a given instance')
parser.add_argument('--instance', type=str, help='SubDomain of your QuablePIM', required=True)
parser.add_argument('--token', type=str, help='Access Token with full permissions', required=True)
args = parser.parse_args()

# Initializing variables
variantCodes = []  # List to store variant IDs
urlGet = "https://{}.quable.com/api/variants?limit=25"  # URL for retrieving variants
urlDelete = "https://{}.quable.com/api_1.php/variants/{}"  # URL for deleting variants
headers = {
    'Authorization': 'Bearer {}'.format(args.token)  # Authorization header with access token
}

# Retrieving all variants
print("Retrieve ALL variants - {}".format(urlGet.format(args.instance)))
response = requests.request("GET", urlGet.format(args.instance), headers=headers)
response_dict = json.loads(response.text)

# Loop to retrieve variants in chunks
for variant in response_dict["hydra:member"]:
    variantCodes.append(variant["id"])

while "hydra:view" in response_dict and "hydra:next" in response_dict["hydra:view"]:
    urlNext = "https://{}.quable.com{}".format(args.instance, response_dict["hydra:view"]["hydra:next"])
    print(" - Retrieve ALL variants - {}".format(urlNext))
    response = requests.request("GET", urlNext, headers=headers)
    response_dict = json.loads(response.text)
    for variant in response_dict["hydra:member"]:
        variantCodes.append(variant["id"])

# Deleting variants one by one
print("Delete variants one by one")
for variantCode in variantCodes:
    print(" - Delete item : '{}'".format(variantCode))
    response = requests.request("DELETE", urlDelete.format(args.instance, variantCode), headers=headers)

# Script completion
print('END')
