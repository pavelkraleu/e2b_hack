# Happy cases

* [Bedřiška Rosenbaumanová](https://github.com/pavelkraleu/e2b_hack/blob/main/research/research_bedřiška_rosenbaumanová.md)

# Parcel Analyzer

This tool analyzes land parcels and their owners, calculating value scores and name uniqueness to help identify the most valuable parcels with uniquely identifiable owners.

## Setup

1. Install dependencies:

```bash
bun i
```

2. Make sure you have a JSONL file with parcel data in the following format:

```jsonl
{"nazev_okresu":"Praha","nazev_obce":"Praha",...}
{"nazev_okresu":"Brno","nazev_obce":"Brno",...}
{"nazev_okresu":"Brno","nazev_obce":"Brno",...}
```

## Usage

Run the analyzer with your JSONL file:

```bash
npm start -- path/to/your/parcels.jsonl
```

The script will:

1. Read the JSONL file
2. Calculate value scores based on:
   - Parcel area (40% weight)
   - Location desirability (60% weight)
3. Calculate name uniqueness scores
4. Combine the scores (70% value, 30% uniqueness)
5. Sort parcels by total score
6. Output results to `analyzed_parcels.jsonl` in the same directory as the input file
7. Display the top 10 most valuable parcels with unique owners

## Customization

You can modify the scoring criteria in the `calculateValueScore` function in `index.ts` to match your specific needs. The current implementation considers:

- Parcel area (normalized)
- Location desirability (based on "downtown" keyword)

## Output

The script generates two types of output:

1. A JSONL file (`analyzed_parcels.jsonl`) containing all analyzed parcels with their scores
2. Console output showing the top 10 most valuable parcels with unique owners
