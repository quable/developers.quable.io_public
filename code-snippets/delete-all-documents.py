# Importing necessary libraries
import argparse  # Library for parsing command-line arguments
import requests  # Library for making HTTP requests
import json      # Library for working with JSON data

# Parsing command-line arguments
parser = argparse.ArgumentParser(description='Remove all documents from a given instance')
parser.add_argument('--instance', type=str, help='SubDomain of your QuablePIM', required=True)
parser.add_argument('--token', type=str, help='Access Token with full permissions', required=True)
args = parser.parse_args()

# Initializing variables
documentCodes = []  # List to store document IDs
urlGet = "https://{}.quable.com/api/documents?limit=25"  # URL for retrieving documents
urlDelete = "https://{}.quable.com/api_1.php/documents/{}"  # URL for deleting documents
headers = {
    'Authorization': 'Bearer {}'.format(args.token)  # Authorization header with access token
}

# Retrieving all documents
print("Retrieve ALL documents - {}".format(urlGet.format(args.instance)))
response = requests.request("GET", urlGet.format(args.instance), headers=headers)
response_dict = json.loads(response.text)

# Loop to retrieve documents in chunks
for document in response_dict["hydra:member"]:
    documentCodes.append(document["id"])

while "hydra:view" in response_dict and "hydra:next" in response_dict["hydra:view"]:
    urlNext = "https://{}.quable.com{}".format(args.instance, response_dict["hydra:view"]["hydra:next"])
    print(" - Retrieve ALL documents - {}".format(urlNext))
    response = requests.request("GET", urlNext, headers=headers)
    response_dict = json.loads(response.text)
    for document in response_dict["hydra:member"]:
        documentCodes.append(document["id"])

# Deleting documents one by one
print("Delete documents one by one")
for documentCode in documentCodes:
    print(" - Delete item : '{}'".format(documentCode))
    response = requests.request("DELETE", urlDelete.format(args.instance, documentCode), headers=headers)

# Script completion
print('END')
