import os
import asyncio
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client, Client
import openai

load_dotenv(override=True)
OPEN_AI_TOKEN = os.getenv("OPEN_AI_CAG")
openai.api_key = OPEN_AI_TOKEN
print(OPEN_AI_TOKEN) ## check
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

## Retrieve all my data from supabase
async def fetch_data():
  print("##### Fetching data from supabase")
  response = supabase.table("trialTable").select('*').execute()
  return response.data ## Returns me a list of the objects

def get_embeddings(texts, model="text-embedding-ada-002"):
    response = openai.embeddings.create(
        input=texts,  # Takes list of strings
        model=model
    )
    return response.data[0].embedding

async def save_embeddings(id, embeddings):
  response = supabase.table("trialTable").update(
      {'embedding': embeddings}
  ).eq('id',id).execute()
  print(response)


def combine_fields(item):
  combinedText = f"{item['term']} - {item['definition']} - {item['explanation']} - {item['additional_resources']}" ## Must use single quotes in formatted string
  return (item['id'], combinedText)

async def main():

  ## Run this section to getEmbeddings for table
  dictionaryData = await fetch_data()
  if dictionaryData:
    for obj in dictionaryData:
      textNid = combine_fields(obj) ## returns me a tuple
      embeddings = get_embeddings(textNid[1]) ## access the combinedText and return me a list of embeddings
      embedding_str = ','.join(map(str, embeddings)) ## converts this to string to store into db
      await save_embeddings(textNid[0], embedding_str)


if __name__ == '__main__':
  asyncio.run(main())
