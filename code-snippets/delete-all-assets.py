# Importing necessary libraries
import argparse  # Library for parsing command-line arguments
import requests  # Library for making HTTP requests
import json      # Library for working with JSON data

# Parsing command-line arguments
parser = argparse.ArgumentParser(description='Remove all assets from a given instance')
parser.add_argument('--instance', type=str, help='SubDomain of your QuablePIM', required=True)
parser.add_argument('--token', type=str, help='Access Token with full permissions', required=True)
args = parser.parse_args()

# Initializing variables
assetCodes = []  # List to store asset IDs
urlGet = "https://{}.quable.com/api/assets?limit=25"  # URL for retrieving assets
urlDelete = "https://{}.quable.com/api_1.php/assets/{}"  # URL for deleting assets
headers = {
    'Authorization': 'Bearer {}'.format(args.token)  # Authorization header with access token
}

# Retrieving all assets
print("Retrieve ALL assets - {}".format(urlGet.format(args.instance)))
response = requests.request("GET", urlGet.format(args.instance), headers=headers)
response_dict = json.loads(response.text)

# Loop to retrieve assets in chunks
for asset in response_dict["hydra:member"]:
    assetCodes.append(asset["id"])

while "hydra:view" in response_dict and "hydra:next" in response_dict["hydra:view"]:
    urlNext = "https://{}.quable.com{}".format(args.instance, response_dict["hydra:view"]["hydra:next"])
    print(" - Retrieve ALL assets - {}".format(urlNext))
    response = requests.request("GET", urlNext, headers=headers)
    response_dict = json.loads(response.text)
    for asset in response_dict["hydra:member"]:
        assetCodes.append(asset["id"])

# Deleting assets one by one
print("Delete assets one by one")
for assetCode in assetCodes:
    print(" - Delete item : '{}'".format(assetCode))
    response = requests.request("DELETE", urlDelete.format(args.instance, assetCode), headers=headers)

# Script completion
print('END')
