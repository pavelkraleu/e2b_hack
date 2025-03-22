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
                
                if person_name:
                    print(f"\nProcessing research for: {person_name}")
                    print(f"Last known location: {last_known_location}")
                    print(f"Property address: {property_address}")
                    
                    try:
                        conduct_research(person_name, last_known_location, property_address)
                        # Add a small delay between requests to avoid rate limiting
                        time.sleep(2)
                    except Exception as e:
                        print(f"Error processing {person_name}: {str(e)}")
                        continue
                else:
                    print("Skipping entry - no person name found")
                    
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON line: {str(e)}")
                continue
            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                continue

if __name__ == "__main__":
    process_parcels() 