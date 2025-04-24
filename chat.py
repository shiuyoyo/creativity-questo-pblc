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
    QType: int = Field(description="Return the types of question student ask as an int 1 or 2")

class GUIDEOutput(BaseModel):
    GUID: str = Field(description="Analyze situation and give non-directive guidance")

class SCAMPEROutput(BaseModel):
    Imprv: str = Field(description="Evaluate the question with suggestions for improvement")
    NewQ: str = Field(description="Provide a revised question")

class LLM:
    def __init__(self):
        self.tknizer = tiktoken.encoding_for_model("gpt-4o-mini")
        self.LLM_Classifier = ChatOpenAI(model="gpt-4o-mini-2024-07-18").with_structured_output(CLSOutput)
        self.LLM_SCAMPER = ChatOpenAI(model="gpt-4o-mini-2024-07-18").with_structured_output(SCAMPEROutput)
        self.LLM_Guidance = ChatOpenAI(model="gpt-4o-mini-2024-07-18").with_structured_output(GUIDEOutput)
        self.activity, self.language = None, 'E'

    def setup_language_and_activity(self, language, activity):
        if activity.strip() == '':
            self.activity_content = "This is a creativity challenge. No specific activity text provided."
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
        cost_input = n_inputs / 1e7 * 0.15

        for output_message in output_messages:
            n_outputs += len(self.tknizer.encode(output_message))
        cost_output = n_outputs / 1e7 * 0.6

        return {'cost_input': cost_input, 'cost_output': cost_output, 'ntkn_input': n_inputs, 'ntkn_output': n_outputs}

    def Chat(self, input_question, language, activity):
        if not all([activity == self.activity, language == self.language]):
            self.setup_language_and_activity(language, activity)

        output_dict = copy.deepcopy(CHAT_INFO_PLACEHOLDER)
        output_dict['MISC']['QUESTION'] = input_question

        # Classification
        cls_message = prompts.CLS_TEMPLATE.replace('{content}', self.activity_content).replace('{question}', input_question)
        QOutput = self.LLM_Classifier.invoke([SystemMessage(content=cls_message)])
        output_dict['INPUT']['CLS'] = cls_message
        output_dict['OUTPUT']['CLS'] = str(QOutput.QType)

        human_message = prompts.USER_TEMPLATE.replace('{question}', input_question)

        if QOutput.QType == 1:
            guide_message = prompts.GUIDE_TEMPLATE.replace('{content}', self.activity_content).replace('{language}', LANGAUGE_DICT[self.language])
            output = self.LLM_Guidance.invoke([
                SystemMessage(content=guide_message),
                HumanMessage(content=human_message),
            ])
            output_dict['INPUT']['GUIDE'] = guide_message
            output_dict['OUTPUT']['GUIDE'] = output.GUID
        elif QOutput.QType == 2:
            element, examples = self.get_element()
            activity_message = prompts.SCAMPER_TEMPLATE.replace('{content}', self.activity_content).replace('{element}', element).replace('{examples}', examples).replace('{language}', LANGAUGE_DICT[self.language])
            output = self.LLM_SCAMPER.invoke([
                SystemMessage(content=activity_message),
                HumanMessage(content=human_message),
            ])
            output_dict['INPUT']['EVAL'] = activity_message
            output_dict['OUTPUT']['EVAL'] = output.Imprv
            output_dict['OUTPUT']['NEWQ'] = output.NewQ
            output_dict['MISC']['SCAMPER_ELEMENT'] = SCAMPER_DICT[element]

        # 成本計算
        input_messages = [v for v in output_dict['INPUT'].values()]
        output_messages = [v for v in output_dict['OUTPUT'].values()]
        cost_dict = self.CalculateCost(input_messages, output_messages)
        output_dict['MISC'].update(cost_dict)

        return output_dict
