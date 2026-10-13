# predict_and_evaluate.py

import sys
import os
import torch
import json
from transformers import DistilBertForQuestionAnswering, DistilBertTokenizerFast
from common_functions import prepare_data, calculate_metrics

pathToSaveModel = sys.argv[1]
testSet = sys.argv[2]

# Extract the base name of the test set to use for the metrics file
testSetName = os.path.basename(testSet).replace('.json', '')  # Remove the file extension
metrics_file = f"metrics_{testSetName}.txt"

# Load the pre-trained DistilBERT model and tokenizer
model = DistilBertForQuestionAnswering.from_pretrained(pathToSaveModel)
tokenizer = DistilBertTokenizerFast.from_pretrained(pathToSaveModel)

# Load the test dataset
with open(testSet, 'r') as f:
    test_data = json.load(f)

# Prepare the test dataset in the correct format
test_dataset = prepare_data(test_data)

# Function to get predictions
def get_predictions(question, context):
    inputs = tokenizer(
        question,
        context,
        truncation=True,
        padding='max_length',
        max_length=384,
        return_tensors="pt"
    )
    
    with torch.no_grad():
        outputs = model(**inputs)

    start_logits = outputs.start_logits
    end_logits = outputs.end_logits
    
    start_index = torch.argmax(start_logits, dim=1).item()
    end_index = torch.argmax(end_logits, dim=1).item()
    
    if end_index < start_index:
        return ""

    tokens = inputs['input_ids'][0][start_index:end_index + 1]
    answer = tokenizer.decode(tokens, skip_special_tokens=True)
    
    return answer if answer.strip() else ""

# Generate predictions on the test dataset
predictions = []
references = []

for i in range(len(test_dataset)):
    example = test_dataset[i]
    print(example['trial_name'])
    question = example['question']
    context = example['context']
    actual_answer = example['answer']['text'][0]

    if not actual_answer:
        print(f"Skipping example {i} due to missing answer.")
        continue

    pred = get_predictions(question, context)

    if pred == "":
        print(f"Prediction is None for example {i}.")

    predictions.append(pred)
    if example['trial_name']=='CLHC165X2101':
        print(pred)
    references.append(actual_answer)

# Calculate and print the metrics
metrics = calculate_metrics(predictions, references)
print(metrics)

# Write metrics to a file
with open(metrics_file, 'w') as f:
    f.write("Evaluation Metrics:\n")
    for metric_name, score in metrics.items():
        f.write(f"{metric_name}: {score:.2f}\n")

print(f"Metrics have been written to {metrics_file}")
