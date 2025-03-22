import json
import sys
import os
from typing import Dict, List, Tuple
from openai import OpenAI
from datetime import datetime

class Parcel:
    def __init__(self, data: Dict):
        # Original Czech attributes
        self.nazev_okresu = data['nazev_okresu']
        self.nazev_obce = data['nazev_obce']
        self.nazev_ku = data['nazev_ku']
        self.opsub_typ = data['opsub_typ']
        self.opsub_rc_ic = data.get('opsub_rc_ic')
        self.opsub_nazev = data['opsub_nazev']
        self.opsub_adresa = data['opsub_adresa']
        self.id_vlastnictvi = data['id_vlastnictvi']
        self.podil_citatel = data['podil_citatel']
        self.podil_jmenovatel = data['podil_jmenovatel']
        self.parcela_vymera = data['parcela_vymera']
        self.nazev_druhu_pozemku = data['nazev_druhu_pozemku']
        self.nazev_zpusobu_vyuziti_pozemku = data.get('nazev_zpusobu_vyuziti_pozemku')
        self.parcela_formatovano = data['parcela_formatovano']
        self.cislo_lv_parcela = data['cislo_lv_parcela']
        self.stavba_nazev_casti_obce = data.get('stavba_nazev_casti_obce')
        self.stavba_nazev_zpusobu_vyuziti = data.get('stavba_nazev_zpusobu_vyuziti')
        self.stavba_formatovano = data.get('stavba_formatovano')
        self.cislo_lv_budova = data.get('cislo_lv_budova')
        self.localid = data['localid']
        self.unique_id = data['unique_id']
        self.polygon = data['polygon']
        self.geo_point = data['geo_point']
        self.group_id = data['group_id']
        self.vlastnena_vymera = data['vlastnena_vymera']
        self.f_country = data['f_country']
        self.color = data['color']
        self.lat_n = data['lat_n']
        self.long_n = data['long_n']
        self.coordinates = data.get('coordinates')
        self.latitude = data.get('latitude')
        self.longitude = data.get('longitude')
        self.owned_by_state = data.get('owned_by_state', False)
        self.id = data['id']

    def to_dict(self) -> Dict:
        return {
            # Original Czech attributes
            'nazev_okresu': self.nazev_okresu,
            'nazev_obce': self.nazev_obce,
            'nazev_ku': self.nazev_ku,
            'opsub_typ': self.opsub_typ,
            'opsub_rc_ic': self.opsub_rc_ic,
            'opsub_nazev': self.opsub_nazev,
            'opsub_adresa': self.opsub_adresa,
            'id_vlastnictvi': self.id_vlastnictvi,
            'podil_citatel': self.podil_citatel,
            'podil_jmenovatel': self.podil_jmenovatel,
            'parcela_vymera': self.parcela_vymera,
            'nazev_druhu_pozemku': self.nazev_druhu_pozemku,
            'nazev_zpusobu_vyuziti_pozemku': self.nazev_zpusobu_vyuziti_pozemku,
            'parcela_formatovano': self.parcela_formatovano,
            'cislo_lv_parcela': self.cislo_lv_parcela,
            'stavba_nazev_casti_obce': self.stavba_nazev_casti_obce,
            'stavba_nazev_zpusobu_vyuziti': self.stavba_nazev_zpusobu_vyuziti,
            'stavba_formatovano': self.stavba_formatovano,
            'cislo_lv_budova': self.cislo_lv_budova,
            'localid': self.localid,
            'unique_id': self.unique_id,
            'polygon': self.polygon,
            'geo_point': self.geo_point,
            'group_id': self.group_id,
            'vlastnena_vymera': self.vlastnena_vymera,
            'f_country': self.f_country,
            'color': self.color,
            'lat_n': self.lat_n,
            'long_n': self.long_n,
            'coordinates': self.coordinates,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'owned_by_state': self.owned_by_state,
            'id': self.id
        }

def calculate_value_score(parcel: Parcel) -> float:
    score = 0.0

    # Area score (normalized)
    score += min(parcel.parcela_vymera / 1000, 1) * 0.4

    # Location desirability
    location_score = 0.6 if 'praha' in parcel.nazev_obce.lower() else 0.3
    score += location_score * 0.6

    return score

async def analyze_names_batch(client: OpenAI, names: List[str], batch_size: int = 50) -> List[Dict]:
    results = []
    for i in range(0, len(names), batch_size):
        batch = names[i:i + batch_size]
        print(f"\nAnalyzing batch {i//batch_size + 1} of {(len(names) + batch_size - 1)//batch_size} ({len(batch)} names)...", flush=True)

        prompt = f'''Analyze these Czech names from the 1930s-1940s period:

{chr(10).join(f'"{name}"' for name in batch)}

For each name, provide a JSON response with:
1. uniquenessScore (0-1): How unique/uncommon is this name? Consider:
   - Common Czech names like "Jan", "Josef", "Marie" should get low scores
   - Uncommon names, especially Jewish names, should get high scores
2. isJewishName (boolean): Is this likely a Jewish name?
3. historicalContext (string): Brief explanation of the name's historical significance

Provide the results as a JSON array, one object per name, in the same order as the input names.

Example response:
[
  {{
    "uniquenessScore": 0.8,
    "isJewishName": true,
    "historicalContext": "Jewish surname with German origin, common among Prague's Jewish community"
  }},
  {{
    "uniquenessScore": 0.3,
    "isJewishName": false,
    "historicalContext": "Common Czech given name and surname"
  }}
]'''

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=4000  # Increased max tokens
                )

                content = response.choices[0].message.content.strip()
                print(f"Response length: {len(content)} characters", flush=True)
                print(f"First 200 chars: {content[:200]}...", flush=True)

                # Try to clean the response if it's not valid JSON
                if not content.startswith('['):
                    import re
                    json_match = re.search(r'\[.*\]', content, re.DOTALL)
                    if json_match:
                        content = json_match.group(0)

                batch_results = json.loads(content)
                print(f"Successfully parsed {len(batch_results)} results", flush=True)

                # Validate the results
                if not isinstance(batch_results, list):
                    raise ValueError("Response is not a list")
                if len(batch_results) != len(batch):
                    raise ValueError(f"Expected {len(batch)} results, got {len(batch_results)}")
                if not all(isinstance(r, dict) and all(k in r for k in ['uniquenessScore', 'isJewishName', 'historicalContext'])
                          for r in batch_results):
                    raise ValueError("Invalid result structure")

                results.extend(batch_results)
                break  # Success, exit retry loop

            except Exception as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}", flush=True)
                print(f"Error type: {type(e)}", flush=True)
                import traceback
                print(f"Traceback: {traceback.format_exc()}", flush=True)

                if attempt < max_retries - 1:
                    print("Retrying with smaller batch size...", flush=True)
                    # Reduce batch size for next attempt
                    batch = batch[:len(batch)//2]
                    if len(batch) < 5:  # If batch is too small, just add default results
                        results.extend([{
                            "uniquenessScore": 0.5,
                            "isJewishName": False,
                            "historicalContext": "Analysis failed"
                        } for _ in batch])
                        break
                else:
                    # All retries failed, add default results
                    results.extend([{
                        "uniquenessScore": 0.5,
                        "isJewishName": False,
                        "historicalContext": "Analysis failed"
                    } for _ in batch])

    print(f"\nTotal results processed: {len(results)}", flush=True)
    return results

async def analyze_parcels(input_file: str, output_file: str):
    print(f"\nStarting analysis at {datetime.now()}", flush=True)

    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # Read the JSONL file
    print(f"Reading parcels from {input_file}...", flush=True)
    parcels: List[Parcel] = []
    with open(input_file, 'r') as f:
        for line in f:
            if line.strip():
                parcels.append(Parcel(json.loads(line)))
    print(f"Loaded {len(parcels)} parcels", flush=True)

    # Get unique names for batch analysis
    unique_names = list(set(p.opsub_nazev for p in parcels))
    print(f"Found {len(unique_names)} unique names to analyze", flush=True)

    # Analyze names in batches
    # name_analyses = await analyze_names_batch(client, unique_names)

    # Create a mapping of names to their analyses
    name_to_analysis = dict(zip(unique_names, name_analyses))

    # Analyze each parcel
    analyzed_parcels = []
    for i, parcel in enumerate(parcels, 1):
        if i % 10 == 0:  # Progress update every 10 parcels
            print(f"Processing parcel {i}/{len(parcels)}...", flush=True)

        value_score = calculate_value_score(parcel)
        name_analysis = name_to_analysis[parcel.opsub_nazev]

        # Calculate name score
        name_score = (
            name_analysis['uniquenessScore'] * 0.6 +
            (0.4 if name_analysis['isJewishName'] else 0)
        )

        # Calculate total score (60% value, 40% name)
        total_score = value_score * 0.6 + name_score * 0.4

        result = parcel.to_dict()
        result.update({
            'valueScore': value_score,
            'nameAnalysis': name_analysis,
            'totalScore': total_score
        })
        analyzed_parcels.append(result)

    # Sort by total score
    print("\nSorting results...", flush=True)
    analyzed_parcels.sort(key=lambda x: x['totalScore'], reverse=True)

    # Write results
    print(f"Writing results to {output_file}...", flush=True)
    with open(output_file, 'w') as f:
        for parcel in analyzed_parcels:
            f.write(json.dumps(parcel) + '\n')

    # Print top 10
    print(f"\nTop 10 most valuable parcels with unique owners:")
    for i, parcel in enumerate(analyzed_parcels[:10], 1):
        print(f"{i}. Parcel {parcel['parcela_formatovano']} - Owner: {parcel['opsub_nazev']}")
        print(f"   Location: {parcel['nazev_obce']}, {parcel['nazev_okresu']}")
        print(f"   Area: {parcel['parcela_vymera']} m²")
        print(f"   Land Type: {parcel['nazev_druhu_pozemku']}")
        print(f"   Value Score: {parcel['valueScore']:.2f}")
        print(f"   Name Analysis:")
        print(f"     - Uniqueness: {parcel['nameAnalysis']['uniquenessScore']:.2f}")
        print(f"     - Jewish Name: {parcel['nameAnalysis']['isJewishName']}")
        print(f"     - Historical Context: {parcel['nameAnalysis']['historicalContext']}")
        print(f"   Total Score: {parcel['totalScore']:.2f}")
        print("---")

    print(f"\nAnalysis completed at {datetime.now()}", flush=True)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python analyze_parcels.py input.jsonl output.jsonl")
        sys.exit(1)

    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    import asyncio
    asyncio.run(analyze_parcels(input_file, output_file))
