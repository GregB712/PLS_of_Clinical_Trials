import numpy as np
import re
import string
from collections import Counter
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
import time
import json

def normalize_answer(s):
    """Lower text and remove punctuation, articles, and extra whitespace."""
    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)
    def white_space_fix(text):
        return ' '.join(text.split())
    def remove_punctuation(text):
        return ''.join(ch for ch in text if ch not in set(string.punctuation))
    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punctuation(lower(s))))

def f1_score(prediction, ground_truth):
    prediction_tokens = normalize_answer(prediction).split()
    ground_truth_tokens = normalize_answer(ground_truth).split()
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0
    precision = 1.0 * num_same / len(prediction_tokens)
    recall = 1.0 * num_same / len(ground_truth_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return f1

def exact_match_score(prediction, ground_truth):
    return normalize_answer(prediction) == normalize_answer(ground_truth)

def bleu_score(prediction, references):
    reference_tokens = [normalize_answer(ref).split() for ref in references]
    prediction_tokens = normalize_answer(prediction).split()
    smoothing = SmoothingFunction().method4
    return sentence_bleu(reference_tokens, prediction_tokens, smoothing_function=smoothing)

def rouge_scores(prediction, reference):
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(normalize_answer(reference), normalize_answer(prediction))
    return scores

def calculate_metrics(predictions, references):
    total_em = 0
    total_f1 = 0
    total_bleu = 0
    total_rouge1 = 0
    total_rouge2 = 0
    total_rougeL = 0

    for prediction, reference in zip(predictions, references):
        total_em += exact_match_score(prediction, reference)
        total_f1 += f1_score(prediction, reference)
        total_bleu += bleu_score(prediction, [reference])
        rouge = rouge_scores(prediction, reference)
        total_rouge1 += rouge['rouge1'].fmeasure
        total_rouge2 += rouge['rouge2'].fmeasure
        total_rougeL += rouge['rougeL'].fmeasure

    n = len(references)
    metrics = {
        "Exact Match": 100.0 * total_em / n,
        "F1 Score": 100.0 * total_f1 / n,
        "BLEU Score": 100.0 * total_bleu / n,
        "ROUGE-1": 100.0 * total_rouge1 / n,
        "ROUGE-2": 100.0 * total_rouge2 / n,
        "ROUGE-L": 100.0 * total_rougeL / n,
        "Number of observations": n
    }

    return metrics

def metricsWrapper(input_file):
    answers = []
    llm_answers = []
    with open(input_file, 'r') as file:
        data = json.load(file)

    counter = 0
    # Iterate over each object in the JSON array and add the 'llm_answer'
    for item in data:
        # print(f'Current trial accessed: {item.get("trial_name", "")}')
        if 'answer' in item.keys() and 'llm_answer' in item.keys():
            answers.append(item.get('answer', ''))
            llm_answers.append(item.get('llm_answer', ''))

    metrics = calculate_metrics(llm_answers, answers)
    print(metrics)

_start = time.time()
files = [
    "How_has_this_trial_helped",
    "How_long_was_the_trial",
    "What_adverse_events_did_participants_report",
    "What_happened_during_the_trial",
    "What_treatments_did_the_participants_take",
    "What_were_the_results_of_the_trial",
    "Who_was_in_this_clinical_trial",
    "Why_was_the_research_needed"
]

print('############################ <Script Logging>: Start calculating metrics')

for file in files:
    start = time.time()
    print('############################################################################################################################################')
    print(f'Current file accessed: {file}')
    input_file = 'FinalDataset/Results/'+ file +'_with_llm_answers.json'
    metricsWrapper(input_file)
    end = time.time()
    elapsedTime = end-start
    print(f'############################ <Script Logging>: Elapsed Time for calculating metrics: {elapsedTime} seconds')
    print('############################################################################################################################################')

_end = time.time()
_elapsedTime = _end-_start
print(f'############################ <Script Logging>: Evaluate.py script has finished in: {_elapsedTime} seconds' )