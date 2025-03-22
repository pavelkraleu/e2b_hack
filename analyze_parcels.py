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

    if parcel.podil_jmenovatel is not None and parcel.podil_jmenovatel > 2:
        return score

    if parcel.nazev_druhu_pozemku is not None and 'vodn' in parcel.nazev_druhu_pozemku.lower():
        return score

    # Area score (normalized)
    score += min(parcel.vlastnena_vymera / 1000, 1) * 0.8

    # Location desirability
    location_score = 0.6 if 'praha' in parcel.nazev_obce.lower() else 0.3
    score += location_score * 0.2

    return score

async def analyze_single_batch(client: OpenAI, batch: List[str], batch_num: int, total_batches: int) -> List[Dict]:
    print(f"\nAnalyzing batch {batch_num} of {total_batches} ({len(batch)} names)...", flush=True)

    prompt = f'''Analyze these Czech names from the 1930s-1940s period:

{chr(10).join(f'"{name}"' for name in batch)}

Return a JSON of {{"names":[{{"name":"Jan Novák","score":0.4,"jewish":true}},{{"name":"Marie Nováková","score":0.2,"jewish":false}}]}} where score is (0-1): How unique/uncommon is this name? Consider: - Common Czech names like "Jan", "Josef", "Marie" should get low scores - Uncommon names, especially Jewish names, should get high scores. and jewish is true if the name is likely jewish.
'''

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            # temperature=0.3,
            response_format={"type": "json_object"},
            stream=False
        )

        content = response.choices[0].message.content.strip()
        print(f"Batch {batch_num} response length: {len(content)} characters", flush=True)
        print(f"Batch {batch_num} first 200 chars: {content[:200]}...", flush=True)

        # Try to clean the response if it's not valid JSON
        if not content.startswith('['):
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)

        batch_results = json.loads(content)
        print(f"Batch {batch_num} successfully parsed {len(batch_results)} results", flush=True)

        # Validate the results
        if not isinstance(batch_results, list):
            raise ValueError("Response is not a list")
        if len(batch_results) != len(batch):
            raise ValueError(f"Expected {len(batch)} results, got {len(batch_results)}")
        if not all(isinstance(r, dict) and all(k in r for k in ['score'])
                  for r in batch_results):
            raise ValueError("Invalid result structure")

        return batch_results

    except Exception as e:
        print(f"Batch {batch_num} failed: {str(e)}", flush=True)
        print(f"Error type: {type(e)}", flush=True)
        import traceback
        print(f"Traceback: {traceback.format_exc()}", flush=True)
        return [{
            "score": 0.0
        } for _ in batch]

async def analyze_names_batch(client: OpenAI, names: List[str], batch_size: int = 100, max_concurrent: int = 20) -> List[Dict]:
    # Split names into batches
    batches = [names[i:i + batch_size] for i in range(0, len(names), batch_size)]
    total_batches = len(batches)
    print(f"\nProcessing {total_batches} batches with {max_concurrent} concurrent requests...", flush=True)

    # Process batches in parallel with a semaphore to limit concurrent requests
    import asyncio
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_batch_with_semaphore(batch: List[str], batch_num: int) -> List[Dict]:
        async with semaphore:
            return await analyze_single_batch(client, batch, batch_num, total_batches)

    # Create tasks for all batches
    tasks = [
        process_batch_with_semaphore(batch, i + 1)
        for i, batch in enumerate(batches)
    ]

    # Wait for all tasks to complete
    results = []
    batch_results = await asyncio.gather(*tasks)

    # Flatten results
    for batch_result in batch_results:
        results.extend(batch_result)

    print(f"\nTotal results processed: {len(results)}", flush=True)
    return results

async def analyze_parcels(input_file: str, output_file: str):
    print(f"\nStarting analysis at {datetime.now()}", flush=True)

    # Read the JSONL file
    print(f"Reading parcels from {input_file}...", flush=True)
    parcels: List[Parcel] = []
    with open(input_file, 'r') as f:
        for i, line in enumerate(f):
            if i >= 10000:
                break
            if line.strip():
                parcels.append(Parcel(json.loads(line)))
    print(f"Loaded {len(parcels)} parcels", flush=True)

    # First calculate value scores for all parcels
    print("\nCalculating value scores...", flush=True)
    parcels_with_scores = []
    for i, parcel in enumerate(parcels, 1):
        if i % 100 == 0:  # Progress update every 100 parcels
            print(f"Processing parcel {i}/{len(parcels)}...", flush=True)

        value_score = calculate_value_score(parcel)
        result = parcel.to_dict()
        result['valueScore'] = value_score
        parcels_with_scores.append(result)

    # Sort by value score and take top 200
    print("\nSorting by value score...", flush=True)
    parcels_with_scores.sort(key=lambda x: x['valueScore'], reverse=True)
    top_parcels = parcels_with_scores[:200]  # Adjust number as needed

    # Get unique names from top parcels for batch analysis
    unique_names = list(set(p['opsub_nazev'] for p in top_parcels))
    print(f"Analyzing {len(unique_names)} unique names from top parcels...", flush=True)

    # If OpenAI API key is set, analyze names in batches
    if os.getenv('OPENAI_API_KEY'):
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        name_analyses = await analyze_names_batch(client, unique_names)
        name_to_analysis = dict(zip(unique_names, name_analyses))
    else:
        name_to_analysis = {name: {'score': 0.0, 'jewish': False} for name in unique_names}

    # Calculate final scores for top parcels
    print("\nCalculating final scores...", flush=True)
    analyzed_parcels = []
    for parcel in top_parcels:
        name_analysis = name_to_analysis[parcel['opsub_nazev']]

        # Calculate name score
        name_score = (
            name_analysis['score'] * 0.6 +
            (0.4 if name_analysis['jewish'] else 0)
        )

        # Calculate total score (30% value, 70% name)
        total_score = parcel['valueScore'] * 0.3 + name_score * 0.7

        parcel.update({
            'nameAnalysis': name_analysis,
            'totalScore': total_score
        })
        analyzed_parcels.append(parcel)

    # Sort by total score
    print("\nSorting by total score...", flush=True)
    analyzed_parcels.sort(key=lambda x: x['totalScore'], reverse=True)

    # Write results
    print(f"Writing results to {output_file}...", flush=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for parcel in analyzed_parcels:
            f.write(json.dumps(parcel, ensure_ascii=False) + '\n')

    # Print top 10
    print(f"\nTop 10 most valuable parcels with unique owners:")
    for i, parcel in enumerate(analyzed_parcels[:10], 1):
        print(f"{i}. Parcel {parcel['parcela_formatovano']} - Owner: {parcel['opsub_nazev']}")
        print(f"   Location: {parcel['nazev_obce']}, {parcel['nazev_okresu']}")
        print(f"   Area: {parcel['parcela_vymera']} m²")
        print(f"   Land Type: {parcel['nazev_druhu_pozemku']}")
        print(f"   Value Score: {parcel['valueScore']:.2f}")
        print(f"   Name Score: {parcel['nameAnalysis']['score']:.2f}")
        print(f"   Total Score: {parcel['totalScore']:.2f}")
        print("---")

    print(f"\nAnalysis completed at {datetime.now()}", flush=True)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python analyze_parcels.py input.jsonl output.jsonl")
        sys.exit(1)

    # # Check for OpenAI API key
    # if not os.getenv('OPENAI_API_KEY'):
    #     print("Error: OPENAI_API_KEY environment variable is not set", file=sys.stderr)
    #     sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    import asyncio
    asyncio.run(analyze_parcels(input_file, output_file))
