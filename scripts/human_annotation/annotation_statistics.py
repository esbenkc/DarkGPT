import json

from sklearn.metrics import cohen_kappa_score

# Load the JSON data from the output
with open("data/human/human-annotation-fixed.json", "r") as file:
    data = json.load(file)

# Define the list of sub-questions to consider
sub_questions = [
    "Privacy zuckering",
    "User retention",
    "Brand awareness",
    "Echo chambers",
    "Cost optimization by answer length",
    "Preference data collection",
    "Anthropomorphization",
    "Harmful generation",
    "Sneaking",
    "Invalid",
    "Demo"
]

# Initialize a dictionary to store the ratings for each sub-question
ratings = {sq: [] for sq in sub_questions}

# Iterate over each annotator's data
for annotator_id, annotator_data in data.items():
    # Iterate over each question
    for question_data in annotator_data["questions"]:
        # Iterate over each sub-question
        for sub_question in sub_questions:
            # Convert the answer to 0 for "No" and 1 for "Yes"
            answer = 0 if question_data.get(sub_question) == "No" else 1
            ratings[sub_question].append(answer)

# Calculate Cohen's Kappa coefficient for each sub-question
kappa_scores = {}
agreement_percentage = {}
count_yes = {}
agreement_on_yes = {}
print(ratings["Privacy zuckering"][::2])
for sub_question in sub_questions:
    kappa = cohen_kappa_score(ratings[sub_question][::2], ratings[sub_question][1::2])
    kappa_scores[sub_question] = kappa
    agreement_percentage[sub_question] = sum([1 for i, j in zip(ratings[sub_question][::2], ratings[sub_question][1::2]) if i == j]) / len(ratings[sub_question][::2])
    count_yes[sub_question] = sum(ratings[sub_question])
    agreement_on_yes[sub_question] = sum([1 for i, j in zip(ratings[sub_question][::2], ratings[sub_question][1::2]) if i == j and i == 1]) / sum(ratings[sub_question])

# Print the Cohen's Kappa coefficient for each sub-question
for sub_question, kappa in kappa_scores.items():
    print(f"**{sub_question}:** kappa = {kappa:.2f}, count_yes = {count_yes[sub_question]}, agreement_percentage = {agreement_percentage[sub_question]:.2f}, agreement_on_yes = {agreement_on_yes[sub_question]}")

# Find some examples of disagreement
disagreements = []
for annotator_id, annotator_data in data.items():
    for question_data in annotator_data["questions"]:
        for sub_question in sub_questions:
            if question_data.get(sub_question) == "Yes":
                if question_data[sub_question] != annotator_data["questions"][0][sub_question]:
                    disagreements.append({
                        "annotator_id": annotator_id,
                        "question": question_data["question"],
                        "sub_question": sub_question,
                        "ai_answer": question_data["ai_model_response"],
                        "annotator_1": annotator_data["questions"][0][sub_question],
                        "annotator_2": question_data[sub_question]
                    })

print("\n\nDisagreements:")
for disagreement in disagreements:
    print(f"Question: {disagreement['question']}")
    print(f"AI Answer: {disagreement['ai_answer']}")
    print(f"Sub-question: {disagreement['sub_question']}")
    print(f"Annotator 1: {disagreement['annotator_1']}")
    print(f"Annotator 2: {disagreement['annotator_2']}")
    print("")
