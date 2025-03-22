# HeirLocator

**HeirLocator** is an autonomous agent designed to assist heir researchers in identifying potential heirs to forgotten properties in the Czech Republic. By automating data processing and online research, it significantly reduces the time and effort required to evaluate a large dataset of [over 400,000 entries of unclaimed land parcels in the country](https://www.uzsvm.gov.cz/informace-pro-verejnost).

## Demovideo

- [Demovideo here](https://www.loom.com/share/db95b1a68b2d43c0b4e4caf418ee8bac)


## 🚨 Problem It Solves

Approximately 120,000 land parcels, with a total estimated value of 0.5 billion USD, have been taken over by the state after being forgotten during inheritance proceedings. Some heirs of the original owners—most of whom were born between 1890 and 1920—could potentially be identified through simple online research using public family trees, local historical records, and wartime documents. However, manually searching through thousands of entries is a tedious and time-consuming task. **HeirLocator** automates this process and helps prioritize the most promising leads.

## ⚙️ How It Works

1. A CSV file containing data about forgotten properties is uploaded to E2B.
2. Within E2B, the file is processed, and properties are sorted by size, estimated value, and uniqueness of the owner names.
3. The top results—based on a combination of value and uniqueness—are passed to the web search agent.
4. The web search agent scrapes top Google results and relevant webpages for information about the given names.
5. The retrieved data is compared with the original input, such as the owner’s name, last known address, and property location.
6. Matches are scored on a confidence scale from 1 to 10, helping researchers focus on the most promising leads.

# Happy cases

- [Bedřiška Rosenbaumanová](https://github.com/pavelkraleu/e2b_hack/blob/main/research/research_bedřiška_rosenbaumanová.md)

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
   - Parcel area (80% weight)
   - Location desirability (20% weight)
3. Calculate name uniqueness scores
4. Combine the scores (30% value, 70% uniqueness)
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
