import os
import copy
import random

import tiktoken
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage

import prompts

LANGAUGE_DICT = {
    'E': 'english',
    'C': 'traditional chinese'
}

SCAMPER_DICT = {
    'S' : 'Substitute',
    'C' : 'Combine',
    'A' : 'Adapt',
    'M' : 'Magnify/Modify',
    'P' : 'Put to other uses',
    'E' : 'Eliminate',
    'R' : 'Re-arrange',
}

CHAT_INFO_PLACEHOLDER = {
    'INPUT':{
        'CLS':'',
        'GUIDE':'',
        'EVAL':'',
    },
    'OUTPUT':{
        'CLS':'',
        'GUIDE':'',
        'EVAL':'',
        'NEWQ':'',
    },
    'MISC':{
        'SCAMPER_ELEMENT': '',
        'QUESTION': ''
    }
}

class CLSOutput(BaseModel):
    QType: int = Field(description="Return the types of question student ask as an int 1 or 2 which type 1 is Question for guidance and 2 is Question for activity")

class GUIDEOutput(BaseModel):
    GUID: str = Field(description="Let's think step by step. Analyze the situation e.g. Pros and Cons, importance of different elements/subjects and encourage the student to make their own analysis and decisions.")

class SCAMPEROutput(BaseModel):
    Imprv: str = Field(description="""Let's think step by step. Evaluate the question's strength and weaknesses with suggestion to improvement based the given SCAMPER element and specificity. The question should always be specific. If the question does not contain a target group or more than one target group, remind the student to pick ONLY ONE specific group to focus on. The evaluation and the suggestions should be specific with detailed explainations with elaborations. Under No cicumstances should you mention or quote the word 'SCAMPER', SCAMPER elements or the definition.""")
    NewQ: str = Field(description= "Based on the improvement you suggested, provide a new and better question.")

class LLM:
    def __init__(self):
        self.tknizer = tiktoken.encoding_for_model("gpt-4o-mini")

        LLM_Classifier = ChatOpenAI(model="gpt-4o-mini-2024-07-18") # Classifier
        self.LLM_Classifier = LLM_Classifier.with_structured_output(CLSOutput)

        LLM_SCAMPER = ChatOpenAI(model="gpt-4o-mini-2024-07-18") # SCAMPER
        self.LLM_SCAMPER = LLM_SCAMPER.with_structured_output(SCAMPEROutput)

        LLM_Guidance = ChatOpenAI(model="gpt-4o-mini-2024-07-18") # GUIDANCE
        self.LLM_Guidance = LLM_Guidance.with_structured_output(GUIDEOutput)

        self.activity, self.language = None, 'E'

    def setup_language_and_activity(self, language, activity):
        # question
        if os.path.isfile(os.path.join('./activities', activity)):
            with open(os.path.join('./activities', activity), 'r') as file:
                file_content = file.read()
            self.activity_content = file_content
        elif activity == '':
            with open('./activities/default.txt', 'r') as file:
                file_content = file.read()
            self.activity_content = file_content
        else:
            self.activity_content = activity
        
        self.language = language.upper()
        self.activity = activity

    def get_element(self):
        element = random.choice([*'SCAMPER'])
        return element, prompts.EXAMPLES[element]

    def CalculateCost(self, input_messages, output_messages):
        n_inputs, n_outputs = 0, 0
        for input_message in input_messages:
            n_inputs += len(self.tknizer.encode(input_message))
        cost_input = n_inputs/1e7 * 0.15

        for output_message in output_messages:
            n_outputs += len(self.tknizer.encode(output_message))
        cost_output = n_outputs/1e7 * 0.6
        
        return {'cost_input': cost_input, 'cost_output': cost_output, 'ntkn_input': n_inputs, 'ntkn_output': n_outputs}

    def Chat(self, input_question, language, activity):
        if not all([activity == self.activity, language == self.language]):
            self.setup_language_and_activity(language, activity)
        

        output_dict = copy.deepcopy(CHAT_INFO_PLACEHOLDER)
        output_dict['MISC']['QUESTION'] = input_question

        # classify question
        cls_message = copy.deepcopy(prompts.CLS_TEMPLATE).replace('{content}', self.activity_content).replace('{question}', input_question)
        QOutput = self.LLM_Classifier.invoke([
            SystemMessage(content = cls_message)
        ])
        output_dict['INPUT']['CLS'] = cls_message
        output_dict['OUTPUT']['CLS'] = str(QOutput.QType)


        human_message = copy.deepcopy(prompts.USER_TEMPLATE).replace('{question}', input_question)

        # guidance question
        if QOutput.QType == 1:
            guide_message = copy.deepcopy(prompts.GUIDE_TEMPLATE).replace('{content}', self.activity_content).replace('{language}', LANGAUGE_DICT[self.language])
            output = self.LLM_Guidance.invoke([
                SystemMessage(content=guide_message),
                HumanMessage(content=human_message),
            ])
            output_dict['INPUT']['GUIDE'] = guide_message
            output_dict['OUTPUT']['GUIDE'] = output.GUID

        # STAMPER question
        elif QOutput.QType == 2:
            element, examples = self.get_element()
            activity_message = copy.deepcopy(prompts.SCAMPER_TEMPLATE).replace('{content}', self.activity_content).replace('{element}', element).replace('{examples}', examples).replace('{language}', LANGAUGE_DICT[self.language])
            output = self.LLM_SCAMPER.invoke([
                SystemMessage(content=activity_message),
                HumanMessage(content=human_message),
            ])
            output_dict['INPUT']['EVAL'] = activity_message
            output_dict['OUTPUT']['EVAL'] = output.Imprv
            output_dict['OUTPUT']['NEWQ'] = output.NewQ
            output_dict['MISC']['SCAMPER_ELEMENT'] = SCAMPER_DICT[element]
        
        # cost calculation
        input_messages = [v for k, v in output_dict['INPUT'].items()]
        output_messages = [v for k, v in output_dict['OUTPUT'].items()]
        cost_dict = self.CalculateCost(input_messages, output_messages)
        output_dict['MISC'].update(cost_dict)

        return output_dict