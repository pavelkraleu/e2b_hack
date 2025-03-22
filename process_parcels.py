import json
from research import conduct_research
import time

def process_parcels():
    with open('analyzed_parcels.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            try:
                parcel = json.loads(line)
                
                # Extract relevant information
                person_name = parcel.get('opsub_nazev')
                last_known_location = parcel.get('opsub_adresa', 'Unknown')
                property_address = parcel.get('parcela_formatovano', 'Unknown')
                localid = parcel.get('localid', 'Unknown')

                print(f"\nProcessing research for: {person_name}")
                print(f"Last known location: {last_known_location}")
                print(f"Property address: {property_address}")
                print(f"Local ID: {localid}")

                conduct_research(person_name, last_known_location, property_address, localid)
                    
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON line: {str(e)}")
                continue


if __name__ == "__main__":
    process_parcels() 