from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
import json
import time

_start = time.time()
# Placeholder function to generate an LLM answer
def generate_llm_answer(context, question):
    result = llm.invoke(prompt.format(context=context, question=question))
    return result

def create_llm_answers(input_file, output_file, input_file2=None):
    with open(input_file, 'r') as file:
        data = json.load(file)

    if input_file2:
        with open(input_file2, 'r') as file2:
            data2 = json.load(file2)
    
    skip_list = []
    for item in data2:
        skip_list.append(item.get("trial_name", ""))

    counter = 0
    # Iterate over each object in the JSON array and add the 'llm_answer'
    for item in data:
        trial_name = item.get("trial_name", "")
        print(f'Current trial accessed: {trial_name}')
        if trial_name in skip_list:
            print('Trial will be skipped!')
            continue
        context = item.get('context', '')
        word_count = count_words(context)
        print(f"The number of words in the context is: {word_count}")
        question = item.get('question', '')
        llm_answer = generate_llm_answer(context, question)
        item['llm_answer'] = llm_answer
        counter = counter + 1
        if counter == 10:
            print('############################ <Script Logging>: Safe point')
            counter = 0
            # Save the updated JSON data to a new file
            with open(output_file, 'w') as file:
                json.dump(data, file, indent=4)

    # Save the updated JSON data to a new file
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=4)

    print(f"Updated JSON data has been saved to {output_file}")

def count_words(string):
    # Split the string into words based on whitespace
    words = string.split()
    # Count the number of words
    word_count = len(words)
    return word_count

print('############################ <Script Logging>: Modules and functions have been loaded!')

# Callbacks support token-wise streaming
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

print('############################ <Script Logging>: Start load model to memory:')

start = time.time()
# Make sure the model path is correct for your system!
llm = LlamaCpp(
    model_path="Mistral-7B-Instruct-v0.1.gguf/mistral-7b-instruct-v0.1.Q5_K_M.gguf",
    temperature=0.75,
    n_ctx=16384,
    max_tokens=2000,
    top_p=1,
    callback_manager=callback_manager,
    verbose=True
)

end = time.time()
elapsedTime = end-start
print('############################ <Script Logging>: Model is now active!')
print(f'############################ <Script Logging>: Elapsed Time for model loading: {elapsedTime} seconds')

# define prompt format to llm
template = """
[INST] 
CONTEXT:
{context}

****************************************************************

QUESTION:
{question}

****************************************************************

INSTRUCTIONS:
Answer the users QUESTION using the CONTEXT text above.
Keep your answer ground in the facts of the CONTEXT and using plain language.
[/INST]
"""

prompt = PromptTemplate.from_template(template)

files = [
    # "How_has_this_trial_helped",
    # "How_long_was_the_trial",
    # "What_adverse_events_did_participants_report",
    # "What_happened_during_the_trial",
    # "What_treatments_did_the_participants_take",
    "What_were_the_results_of_the_trial",
    # "Who_was_in_this_clinical_trial",
    # "Why_was_the_research_needed"
]

print('############################ <Script Logging>: Start generating answers')

for file in files:
    start = time.time()
    print('############################################################################################################################################')
    print(f'Current file accessed: {file}')

    input_file = 'FinalDataset/FullDataset2/FullDataset2/'+ file +'.json'
    input_file2 = 'FinalDataset/FullDataset2/'+ file +'.json'
    output_file = 'FinalDataset/Results2/'+ file +'_with_llm_answers.json'
    create_llm_answers(input_file, output_file, input_file2)
    end = time.time()
    elapsedTime = end-start
    print(f'############################ <Script Logging>: Elapsed Time for generating LLM answers: {elapsedTime} seconds')
    print('############################################################################################################################################')

_end = time.time()
_elapsedTime = _end-_start
print(f'############################ <Script Logging>: Pretrained.py script has finished in: {_elapsedTime} seconds' )