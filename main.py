import os
import sys
import glob
import json
import argparse
import datetime
import textwrap
import logging

from chat import LLM

SAVE_ROOT = './llm_outputs'

def print_and_save(question_idx, input_, llm_response):
    str_ = ''
    str_ += f'#{question_idx} {input_}\nLLM Response:\n'
    if llm_response['OUTPUT']['CLS'] == '1':
        str_ += 'Analysis: ' + textwrap.fill(llm_response['OUTPUT']['GUIDE'], width = 120) + '\n'
    elif llm_response['OUTPUT']['CLS'] == '2':
        str_ += 'Analysis: ' + textwrap.fill(llm_response['OUTPUT']['EVAL'], width = 120) + '\n'
        str_ += 'Suggestion: ' + textwrap.fill(llm_response['OUTPUT']['NEWQ'], width = 120) + '\n'
        str_ += f"SCAMPER element: {llm_response['MISC']['SCAMPER_ELEMENT']}\n"
    else:
        str_ += f'The input does not seems to be a question. Please try again!\n'
    str_ += f"Inference Cost: {llm_response['MISC']['cost_input'] + llm_response['MISC']['cost_output']:.6f}\n\n"

    print(str_)
    return str_

def collect_options():
    language = input('Please input prefered language (English or Chinese). Enter E or C only: ')
    assert language.upper() in ['E', 'C'], 'Please only enter "E" or "C"!'
    activity = input('Please input the activity: ')

    return language, activity

def stream():
    save_dir = os.path.join(SAVE_ROOT, datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(save_dir, exist_ok=True)

    llm = LLM()
    language, activity = collect_options()
    output_for_save = ''

    question_idx = 0
    while True:
        input_ = input('Type in your question, "Z" to reset language and activity, or "END" to end the chat: ')
        if input_.upper() == 'END':
            break
        elif input_.upper() == 'Z':
            language, activity = collect_options()
        else:
            llm_response = llm.Chat(input_, language, activity)
            output_for_save += print_and_save(question_idx, input_, llm_response)

            # save output
            with open(os.path.join(save_dir, f'QnA_{str(question_idx).zfill(3)}.json'), 'w') as file:
                json.dump(llm_response, file, indent=4)

            question_idx += 1
            
    with open(os.path.join(save_dir,"output.txt"), "w") as text_file:
        text_file.write(output_for_save)    
    

def load_file():
    save_dir = os.path.join(SAVE_ROOT, datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(save_dir, exist_ok=True)

    llm = LLM()
    language, activity = collect_options()
    questions = input('Type in question filename: ')
    if questions == '':
        import default_questions
        questions = default_questions.eng_questions if language.upper() == 'E' else default_questions.chin_questions
    else:
        with open(questions, 'r') as file:
            questions = file.read()
                    
    output_for_save = ''
    for question_idx, input_ in enumerate(questions.split(';')):
        llm_response = llm.Chat(input_, language, activity)
        output_for_save += print_and_save(question_idx, input_, llm_response)

        # save output
        with open(os.path.join(save_dir, f'QnA_{str(question_idx).zfill(3)}.json'), 'w') as file:
            json.dump(llm_response, file, indent=4)
        
    with open(os.path.join(save_dir,"output.txt"), "w") as text_file:
        text_file.write(output_for_save)

if __name__ == '__main__':
    parser = argparse.ArgumentParser("SCAMPER Project - LLM Chatbot to improve student creativity")
    parser.add_argument("--load_file", action = 'store_true', help='load file instead of streaming')
    parser.add_argument("--local", action = 'store_true', help='Wrapper to please git')
    args = parser.parse_args()

    if args.local:
        from api_key import OPENAI_API_KEY
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

    if args.load_file:
        load_file()
    else:
        stream()

