import json
from groq import Groq
import os       

class AssignPois:
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)

    @staticmethod
    def extract_dict(response_str, default=None):
        try:
            stack = []
            last_dict = None
            start_idx = -1

            # Iterate through the response to track { and } positions
            for i, char in enumerate(response_str):
                if char == '{':
                    if not stack:
                        start_idx = i  # Mark the start of a new dictionary
                    stack.append(i)
                elif char == '}':
                    if stack:
                        stack.pop()  # Remove last open brace
                        if not stack:
                            last_dict = response_str[start_idx:i + 1]  # Capture last complete dict

            if not last_dict:
                return default

            # Fix potential JSON formatting issues
            last_dict = last_dict.replace("'", '"')  # Convert single quotes to double quotes
            last_dict = last_dict.replace(', }', '}')  # Remove trailing commas before }

            # Generic helper to fix a field's value by escaping inner quotes
            def fix_field(json_str, key):
                key_str = f'"{key}": "'
                key_start = json_str.find(key_str)
                if key_start == -1:
                    return json_str  # Field not found, return unchanged
                start_value = key_start + len(key_str)
                i = start_value
                escaped = False
                fixed_chars = []
                while i < len(json_str):
                    c = json_str[i]
                    # If we encounter an unescaped quote, decide if it's the closing quote or needs escaping
                    if c == '"' and not escaped:
                        # Peek ahead to decide if this is the closing quote.
                        j = i + 1
                        while j < len(json_str) and json_str[j].isspace():
                            j += 1
                        if j < len(json_str) and json_str[j] in [',', '}']:
                            # This is likely the closing quote for the field value.
                            break
                        else:
                            # This is an inner quote that needs escaping.
                            fixed_chars.append('\\"')
                            i += 1
                            continue  # Skip appending the original quote
                    else:
                        fixed_chars.append(c)
                    if c == '\\' and not escaped:
                        escaped = True
                    else:
                        escaped = False
                    i += 1
                corrected_value = ''.join(fixed_chars)
                # Replace the original field value with the corrected one.
                return json_str[:start_value] + corrected_value + json_str[i:]
            
            # Fix the "name" and "description" fields
            last_dict = fix_field(last_dict, "name")
            last_dict = fix_field(last_dict, "description")

            # Debug print
            print("Extracted JSON String:", last_dict)

            # Convert to Python dictionary
            real_dict = json.loads(last_dict)
            return real_dict

        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return default
            
    @staticmethod
    def generate_response(prompt, default=None):
        retries = 3
        delay = 5  # seconds

        for attempt in range(retries):
            try:
                completion = AssignPois.client.chat.completions.create(
                    model="deepseek-r1-distill-llama-70b",
                    messages=prompt,
                    temperature=0.5,
                    max_completion_tokens=5000,
                    top_p=0.95,
                    stream=False
                )
                raw_resp = completion.choices[0].message.content
                return AssignPois.extract_dict(raw_resp, default)

            except Exception as e:
                if "429" in str(e):  # Handle rate limiting
                    return "Limit Exceeded"
                elif "400" in str(e):
                    raise e
                else:
                    raise e
    
    @staticmethod
    def prompt(desc, dict):
        return [
            {
                "role": "system",
                "content": "Given an image description and a list of dictionaries of poi names and their descriptions, assign the image to the most relevant poi. You MUST return a response, even if it is not ideal. Return ONLY the python poi dictionary. eg. {\"name\": \"Times Square\", \"description\": \"Times Square in New York City is one of the most iconic and bustling places on Earth.\"}"
            },
            {
                "role": "user",
                "content": desc + "\n\n" + str(dict)
            }
        ]
        
# Path to your JSONL file
file_path = "poo.jsonl"
output_path = "raw.jsonl"

successful_entries = 0  # Counter for successful entries

with open(file_path, "r", encoding="utf-8") as infile, open(output_path, "a", encoding="utf-8") as outfile:  # Changed mode from "w" to "a" for appending
    for line in infile:
        entry = json.loads(line)  # Parse JSON line
        processed_entry = True  # Track if the entire entry processes correctly

        for msg in entry.get("messages", []):
            if msg["role"] == "user" and isinstance(msg.get("content"), dict):
                img_pois = []
                images = msg["content"].get("images", [])
                pois = msg["content"].get("pois", [])
                
                for image in images:
                    desc = image["description"]
                    resp = AssignPois.generate_response(AssignPois.prompt(desc, pois), pois[0])
                    
                    if resp == "Limit Exceeded":
                        print(f"{successful_entries} entries entered successfully before hitting the limit.")
                        exit()

                    # if resp in pois:
                    #     pois.remove(resp)
                    img_pois.append({desc: resp})
                
                msg["content"] = img_pois #{"image_pois": img_pois, "remaining_pois": pois}

        if processed_entry:
            outfile.write(json.dumps(entry, ensure_ascii=False) + "\n")
            successful_entries += 1  # Increment only for fully processed entries

print(f"Processing complete. {successful_entries} entries entered successfully. Output saved to {output_path}.")
