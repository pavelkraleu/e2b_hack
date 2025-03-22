import requests
import json
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
import os
import hashlib
import pathlib
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

# person_name = "Bedřiška Rosenbaumanová"
# last_known_location = "Unknown"
# property_address = "Úvaly"

# person_name = "Helena Blacková"
# last_known_location = "Omaha, Spojené státy"
# property_address = "Holešovice, č. 994"

# person_name = "Arnošt Stadler"
# last_known_location = "unknown"
# property_address = "Praha-Vršovice, č. 2449/1"

def get_cache_path(url):
    """Generate a cache file path for a given URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_dir = pathlib.Path('.cache')
    return cache_dir / f"{url_hash}.json"

def get_cached_response(url):
    """Retrieve cached response if it exists."""
    cache_path = get_cache_path(url)
    if cache_path.exists():
        with open(cache_path, 'r') as f:
            return json.load(f)
    return None

def cache_response(url, response):
    """Cache the response for a given URL."""
    cache_path = get_cache_path(url)
    with open(cache_path, 'w') as f:
        json.dump(response, f)

def conduct_research(person_name, last_known_location, property_address, localid):
    url = "https://google.serper.dev/search"

    payload = json.dumps({
      "q": person_name,
      "gl": "cz"
    })
    headers = {
      'X-API-KEY': os.getenv('SERPER_API_KEY'),
      'Content-Type': 'application/json'
    }

    app = FirecrawlApp(api_key=os.getenv('FIRECRAWL_API'))

    response = requests.request("POST", url, headers=headers, data=payload)

    respo_json = response.json()

    # Initialize list to store markdowns
    markdowns = []

    for url in respo_json["organic"]:
        print(f"Processing URL: {url['link']}")
        if "xls" in url['link'] or "pdf" in url['link']:
            continue

        cached_response = get_cached_response(url["link"])
        if cached_response:
            response = cached_response
        else:
            try:
                response = app.scrape_url(
                    url=url["link"], params={
                        'formats': ['markdown'],
                    })
                cache_response(url["link"], response)
            except Exception as e:
                print(f"Failed to scrape URL {url['link']}: {str(e)}")
                continue

        # Add markdown to our collection with triple backticks and source URL
        markdowns.append(f"Source: {url['link']}\n```md\n{response['markdown']}\n```")

    # Construct the prompt
    prompt = f"""Based on the following Internet searches about {person_name}, please provide a comprehensive summary.
    
    This person is known to be from {last_known_location} and to own a property at {property_address}.
    Person was born approximately between 1890 and 1930.
    We are interested in this person family so we can reach out to them regarding the lost property.
    
    Internet searches are not always accurate, it may include information about other people with the same name.
    
    Mention only information from the Internet searches, ignore other information and don't make up any information.
    
    {'\n---\n'.join(markdowns)}
    
    Please analyze the above information and provide:
    - A brief biography
    - Family members
    - Any other relevant information
    - Fate of the person
    - Format output in Markdown
    - Include links to relevant sources
    """

    print("\nGenerated Prompt:")
    print(prompt)

    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful research assistant analyzing historical information about people and their families."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )


    markdown_summary = response.choices[0].message.content
    markdown_summary = markdown_summary.replace("```markdown", "").replace("`", "")

    print(markdown_summary)

    class PersonSummary(BaseModel):
        exact_person_found: bool = Field(description="Whether the person was found in the Summary")
        exact_person_found_rating: int = Field(description="Rating of the exact person found, from 0 to 10")
        exact_person_found_reason: str = Field(description="Reason for exact person found, describe which information matched and reasoning behind it")
        years_of_life: str = Field(description="Years of life of the person")
        family_members: list[str] = Field(description="Family members of the person")
        fate_of_the_person: str = Field(description="Fate of the person")
        images_urls: list[str] = Field(description="Important images")

    system_prompt = f"""You are a helpful research assistant analyzing historical information about people and their families.
    
    You are given a Summary of the research about {person_name}, last known location {last_known_location} and property at {property_address}.
    The only information we we know about the person is that they lived in {last_known_location} and owned a property at {property_address}.
    
    When you are working with very unique name and found exactly this name, it is very likely that this is the person we are looking for.
    
    Summary is not always accurate, it is mainly Google search results, so you need to reason about it and provide your own conclusion.
    We can't be sure if the person mentioned in the Summary is the same person, so you need to reason about it and provide your own conclusion.
    
    """

    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": markdown_summary},
        ],
        response_format=PersonSummary,
    )

    summary = completion.choices[0].message.parsed

    print(summary)

    # Combine summaries into a single Markdown document
    combined_markdown = f"""# {person_name}

## Last known information about the person
- Name: {person_name}
- Last known location: {last_known_location}
- Property at: {property_address} 
- [PZMK](https://pzmk.cz/{localid})

## Research Summary
- **Exact Person Found**: {'Yes' if summary.exact_person_found else 'No'}
  - **Exact Person Found Rating (1/10)**: {summary.exact_person_found_rating}
  - **Reason for Exact Person Found**: {summary.exact_person_found_reason}
- **Years of Life**: {summary.years_of_life}
- **Family Members**: {', '.join(summary.family_members)}
- **Fate**: {summary.fate_of_the_person}

{f'## Important Images\n{chr(10).join(f"![Historical Image]({url})" for url in summary.images_urls)}\n\n' if summary.images_urls else ''}---

## Detailed Research
{markdown_summary}
    """

    # Save the combined markdown to a file
    output_file = f"research/research_{person_name.lower().replace(' ', '_')}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(combined_markdown)

    print(f"\nCombined research summary has been saved to {output_file}")


# person_name = "Arnošt Stadler"
# last_known_location = "unknown"
# property_address = "Praha-Vršovice, č. 2449/1"

# conduct_research("Josefa Perluszová", "P9 J.Jabůrkové 6/17", "Vysočany, č. 16/1", "2109591101")
conduct_research("Fiala Jeroným JUDr.", "Hvězdova 59, Nusle, 14000 Praha", "Břevnov, č. 3563", "2109591101")