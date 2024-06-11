import json
import re

# Load the JSON data from the document content
with open("data/human/human-annotations.json", "r") as file:
    document_content = file.read()
json_data = json.loads(document_content)

# Initialize a dictionary to store the extracted data
data = {}

# Iterate over each response
for response in json_data["responses"]:
    response_id = response["Response ID"]
    data[response_id] = {}

    # Extract metadata
    metadata_keys = ["Date submitted", "Last page", "Start language", "Seed", "Date started",
                     "Date last action", "IP address", "Referrer URL"]
    for key in metadata_keys:
        data[response_id][key] = response[key]
    data[response_id]["questions"] = []

    # Extract questions and sub-questions
    for key, value in response.items():
        if key.startswith("   Human:"):
            question = key.split("Human:")[-1].split("AI model:")[0].strip()
            ai_model_response = key.split("AI model:")[-1].strip()
            sub_questions = re.findall(r"\[(.+?)\]", key)

            # Check if question already exists in dataset, if it does, append the sub-question
            question_exists = False
            question_index = None
            for question_data in data[response_id].get("questions", []):
                if question_data["question"] == question:
                    question_exists = True
                    question_index = data[response_id]["questions"].index(question_data)
                    break

            if question_exists:
                data[response_id]["questions"][question_index][sub_questions[-1]] = value.strip()
            else:
                question_data = {
                    "question": question,
                    "ai_model_response": ai_model_response,
                    sub_questions[-1]: value.strip()
                }

                data[response_id].setdefault("questions", []).append(question_data)


# Convert the extracted data to JSON format
output_json = json.dumps(data, indent=2)

# Write the output JSON to a file
with open("data/human/human-annotation-fixed.json", "w") as file:
    file.write(output_json)
