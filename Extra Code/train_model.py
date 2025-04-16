# train_model.py

import sys
from transformers import DistilBertForQuestionAnswering, DistilBertTokenizerFast, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
import json

from common_functions import prepare_data

pathToSaveModel = sys.argv[1]
trainSet = sys.argv[2]

# Load the pre-trained DistilBERT model and tokenizer
model = DistilBertForQuestionAnswering.from_pretrained('distilbert-base-uncased')
tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')

# Load the training dataset
with open(trainSet, 'r') as f:
    train_data = json.load(f)

# Prepare the dataset in the correct format
full_train_dataset = prepare_data(train_data)

# Split the training data into training and validation sets
train_size = 0.8  # 80% for training, 20% for validation
train_indices, val_indices = train_test_split(list(range(len(full_train_dataset))), train_size=train_size, random_state=42)

train_dataset = full_train_dataset.select(train_indices)
eval_dataset = full_train_dataset.select(val_indices)

# Preprocessing function
def preprocess_function(examples):
    inputs = tokenizer(
        examples['question'], 
        examples['context'], 
        truncation=True, 
        padding='max_length', 
        max_length=384,
        return_offsets_mapping=True
    )
    
    offset_mapping = inputs.pop("offset_mapping")
    start_positions = []
    end_positions = []

    for i, offset in enumerate(offset_mapping):
        answer = examples["answer"][i]
        start_char = answer["answer_start"][0]
        end_char = start_char + len(answer["text"][0])

        sequence_ids = inputs.sequence_ids(i)

        context_start = sequence_ids.index(1)
        context_end = len(sequence_ids) - 1 - sequence_ids[::-1].index(1)

        if offset[context_start][0] > end_char or offset[context_end][1] < start_char:
            start_positions.append(0)
            end_positions.append(0)
        else:
            start_idx = context_start
            end_idx = context_end
            while start_idx <= context_end and offset[start_idx][0] <= start_char:
                start_idx += 1
            while end_idx >= context_start and offset[end_idx][1] >= end_char:
                end_idx -= 1
            start_positions.append(start_idx - 1)
            end_positions.append(end_idx + 1)

    inputs["start_positions"] = start_positions
    inputs["end_positions"] = end_positions
    return inputs

# Apply the preprocessing function to the datasets
tokenized_train_dataset = train_dataset.map(preprocess_function, batched=True, remove_columns=train_dataset.column_names)
tokenized_eval_dataset = eval_dataset.map(preprocess_function, batched=True, remove_columns=eval_dataset.column_names)

# Set training arguments
training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",  # Evaluate at the end of each epoch
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    weight_decay=0.01,
    save_strategy="epoch",
)

# Initialize Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train_dataset,
    eval_dataset=tokenized_eval_dataset,
    tokenizer=tokenizer,
)

# Train the model
trainer.train()

# Save the model
model.save_pretrained(pathToSaveModel)
tokenizer.save_pretrained(pathToSaveModel)
