import os
import qdrant_client
from dotenv import load_dotenv
from tsp_solver import TSPSolver
from sentence_transformers import SentenceTransformer
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import ast

# Load environment variables
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Load Qdrant client
client = qdrant_client.QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
print("Connected to Qdrant.")

# Load Sentence Transformer model for embeddings
encoder = SentenceTransformer("all-MiniLM-L6-v2")
print("Loaded SentenceTransformer.")

# Initialize LLM (DeepSeek 70B)
chat_model = ChatGroq(temperature=0, model_name="deepseek-r1-distill-llama-70b")
print("Loaded DeepSeek model.")

# Define a system prompt for context-aware responses
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert travel assistant helping users find the best itineraries. "
               "You provide engaging and detailed responses based on available itineraries and the user's conversation history."),
    ("human", "Here is the conversation history so far:\n\n{history}\n\n"
              "Based on the following itineraries, combine them in a way to suggest the best, most relevant plan. Position pois in logical geographic travelling order to avoid backtracking and group closer pois by day: \n\n{context}\n\n"
              "User query: {question}\n\nProvide a comprehensive sequence of pois and corresponding descriptions with time stamps to be as relevant and on point to the query as possible."),
    ("human", "The second thing to return is a python dictionary with keys as day numbers and values as a list of all the poi location names of the day where the first value is the city name. e.g. 1: [\"Paris\", \"Louvre Museum\", \"Notre Dame\"]")
 ])

# Qdrant search function
def search_itineraries(query, top_k=4):
    query_vector = encoder.encode(query).tolist()
    hits = client.search(collection_name="itineraries_data", query_vector=query_vector, limit=top_k)

    itineraries = []
    urls = []  # Store URLs for the top itineraries
    for hit in hits:
        if hit.score > 0.5:
            itineraries.append(hit.payload["content"])
            urls.append(hit.payload["metadata"]["url"])  # Extract URLs

    return itineraries, urls


# Function to get a response while maintaining conversation history
def get_response(query, history):
    relevant_itineraries, urls = search_itineraries(query)  # Get itineraries and URLs
    response = ""
    context = "\n\n".join(relevant_itineraries)
    messages = chat_prompt.format_messages(history=history, context=context, question=query)
    response = chat_model.invoke(messages).content

    return response

def get_raw_response(history, query):
    chat_prompt_2 = ChatPromptTemplate.from_messages([
    ("system", "You are an expert travel assistant that creates itineraries."),
    ("human", f"The request is to create a {query}"),
    ("human", "Return a python dictionary with keys as day numbers and values as a list of all the poi location names of the day where the first value is the city name provided. e.g. 1: [\"Paris\", \"Louvre Museum\", \"Notre Dame\"... (etc)]")
    ])
    response = ""
    messages = chat_prompt_2.format_messages(history=history, question=query)
    response = chat_model.invoke(messages).content

    return response


def parse_string(string):
    return ast.literal_eval(string)

def add_city_for_text(itineraries):
    for day in itineraries.values():
        city = day.pop(0)
        for i in range(len(day)):
            day[i] = day[i] + f", {city}"

    return itineraries

def google_maps_links(itineraries):
    links = []
    for day in itineraries.values():
        link = "https://www.google.com/maps/dir/"
        for loc in day:
            link += str(loc[0]) + "," + str(loc[1])
            link += "/"
        links.append(link)
    
    return links

# Loop code for manual terminal testing
def main():
    print("\nWelcome to the AI Travel Assistant! Type 'exit' to quit.\n")

    history = []  # Stores the conversation history

    while True:
        user_query = input("Enter your travel query: ").strip()
        if user_query.lower() == "exit":
            print("Goodbye!")
            break
        
        response_rag = get_response(user_query, " ".join(history[-5:]))
        pois_dict_rag = parse_string(response_rag[response_rag.find("{") : response_rag.find("}") + 1].replace("#", "").replace("*", "").replace("`", "").replace("\n", ""))
        pois_dict_ll, pois_dict_text = TSPSolver.reorder(add_city_for_text(pois_dict_rag))
        # pois_dict_rag_clean = add_city(pois_dict_rag)
        links = google_maps_links(pois_dict_ll)
        print("Here are the google maps trajectories for each day.")
        for count in range(len(links)):
            print(f"Day {str(count + 1)} Google Maps Trajectory:", end = " ")
            print(links[count])


if __name__ == "__main__":
    main()