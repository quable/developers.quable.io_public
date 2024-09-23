import requests
import logging
import sys
import argparse

linksToRemove = [{
    "linkTypeId" : "x-sell",
    "originId" : "sweat-blue",
    "targetId" : "sweat-pink",
},{
    "linkTypeId" : "x-sell",
    "originId" : "sweat-pink",
    "targetId" : "sweat-black",
},{
    "linkTypeId" : "x-sell",
    "originId" : "sweat-pink",
    "targetId" : "sweat-red",
}]

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def remove_links(pim_instance, api_token, links_to_remove):
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    for link in links_to_remove:
        link_type_id = link.get("linkTypeId")
        origin_id = link.get("originId")
        target_id = link.get("targetId")
        
        try:
            # Appel GET pour vérifier les liens existants
            url = f'https://{pim_instance}.quable.com/api/links?linkType.id={link_type_id}&origin.id={origin_id}&target.id={target_id}'
            logging.info(f"Checking link: {link_type_id} from {origin_id} to {target_id}")
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Gérer les erreurs HTTP

            data = response.json()
            
            # Vérifier si des liens existent
            if response.status_code == 200 and data.get('hydra:totalItems', 0) > 0:
                logging.info(f"Found {data['hydra:totalItems']} link(s) to remove.")
                
                # Parcourir les éléments à supprimer
                for member in data.get('hydra:member', []):
                    link_id = member.get('id')
                    if link_id:
                        delete_url = f'https://{pim_instance}.quable.com/api/links/{link_id}'
                        logging.info(f"Deleting link with ID: {link_id}")
                        delete_response = requests.delete(delete_url, headers=headers)
                        delete_response.raise_for_status()  # Vérifier la suppression
                        if delete_response.status_code == 204:
                            logging.info(f"Successfully deleted link with ID: {link_id}")
                        else:
                            logging.warning(f"Failed to delete link with ID: {link_id}")
            else:
                logging.info(f"No links found for: {link_type_id} from {origin_id} to {target_id}")
        
        except requests.exceptions.RequestException as e:
            logging.error(f"Error occurred while processing link {link_type_id} from {origin_id} to {target_id}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            sys.exit(1)  # Stopper le script en cas d'erreur grave

if __name__ == "__main__":
    # Parser les arguments
    parser = argparse.ArgumentParser(description="Script to remove links from PIM instance")
    parser.add_argument('pim_instance', type=str, help="PIM instance URL (e.g. https://{pim_instance}.quable.com)")
    parser.add_argument('api_token', type=str, help="API token for authentication")
    
    args = parser.parse_args()
    
    # Appel de la fonction avec les arguments fournis
    remove_links(args.pim_instance, args.api_token, linksToRemove)
