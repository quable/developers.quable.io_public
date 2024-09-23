import csv
import requests
import logging
import argparse
import os

# Set up logging configuration
logging.basicConfig(filename='pim_api.log', level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

def process_csv(api_token, pim_instance, csv_file):
    """
    Processes the CSV file and sends classification updates to the PIM API.

    Parameters:
        api_token (str): API access token.
        pim_instance (str): PIM instance URL.
        csv_file (str): Path to the CSV file.
    """
    try:
        # Check if the file exists and is readable
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"File '{csv_file}' not found.")

        with open(csv_file, newline='') as csvfile:
            csvreader = csv.DictReader(csvfile)

            for row in csvreader:
                document_code = row['document_code']
                classification = row['classification_code']

                # Headers to include the access token in the request
                headers = {
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "classification_code": classification
                }

                # Construct the request URL
                url = f"https://{pim_instance}.quable.com/api_1.php/documents/{document_code}"

                # Send the request to update classification
                response = requests.put(url, json=payload, headers=headers)

                if response.status_code == 200:
                    message = f"Successfully assigned classification '{classification}' to document '{document_code}'."
                    logging.info(message)
                    print(message)
                else:
                    message = f"Error assigning classification '{classification}' to document '{document_code}': {response.text}"
                    logging.error(message)
                    print(message)

    except FileNotFoundError as e:
        logging.error(f"CSV file error: {e}")
        print(f"Error: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP request failed: {e}")
        print(f"HTTP request failed: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    # Argument parser for command-line execution
    parser = argparse.ArgumentParser(description='Process CSV file and update PIM API classifications.')
    parser.add_argument('--api_token', required=True, help='API access token.')
    parser.add_argument('--pim_instance', required=True, help='PIM instance (e.g., your_instance.quable.com).')
    parser.add_argument('--csv_file', required=True, help='Path to the CSV file.')

    # Parse arguments
    args = parser.parse_args()

    # Validate the token
    if len(args.api_token) < 20:
        raise ValueError("The provided API token seems too short. Please check your token.")

    # Execute the CSV processing
    process_csv(args.api_token, args.pim_instance, args.csv_file)
