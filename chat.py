import os
import copy
import random
import time
import streamlit as st

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
        self.tknizer = tiktoken.encoding_for_model("gpt-3.5-turbo")  # 改用3.5的tokenizer
        
        # ✅ 加入模型配置選項
        self.model_config = {
            "cheap": "gpt-3.5-turbo",  # 便宜選項
            "free": "gpt-3.5-turbo",   # 免費額度選項  
            "premium": "gpt-4o-mini"   # 高品質選項
        }
        
        # ✅ 根據環境變數或設定選擇模型
        self.model_choice = os.getenv("QST_MODEL_TIER", "cheap")  # 預設使用便宜選項
        self.selected_model = self.model_config.get(self.model_choice, "gpt-3.5-turbo")
        
        # ✅ 改進：嘗試從不同來源獲取 API Key
        api_key = self._get_api_key()
        
        if not api_key:
            st.error("⚠️ OpenAI API Key not found! Please set it in Streamlit Secrets or environment variables.")
            self.api_available = False
            return
            
        # ✅ 加入錯誤處理的 LLM 初始化 - 使用選定的模型
        try:
            st.info(f"🤖 Using model: {self.selected_model} (Cost-saving mode)")
            
            LLM_Classifier = ChatOpenAI(
                model=self.selected_model,
                api_key=api_key,
                max_retries=2,
                request_timeout=30,
                temperature=0.3  # 降低temperature以節省成本
            )
            self.LLM_Classifier = LLM_Classifier.with_structured_output(CLSOutput)

            LLM_SCAMPER = ChatOpenAI(
                model=self.selected_model,
                api_key=api_key,
                max_retries=2,
                request_timeout=30,
                temperature=0.7
            )
            self.LLM_SCAMPER = LLM_SCAMPER.with_structured_output(SCAMPEROutput)

            LLM_Guidance = ChatOpenAI(
                model=self.selected_model,
                api_key=api_key,
                max_retries=2,
                request_timeout=30,
                temperature=0.5
            )
            self.LLM_Guidance = LLM_Guidance.with_structured_output(GUIDEOutput)

            self.activity, self.language = None, 'E'
            self.api_available = True
            
        except Exception as e:
            st.error(f"Failed to initialize LLM models: {e}")
            self.api_available = False

    def _get_api_key(self):
        """嘗試從不同來源獲取 API Key"""
        # 1. 嘗試從 Streamlit secrets
        if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
        
        # 2. 嘗試從環境變數
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return api_key
            
        # 3. 如果都沒有，返回 None
        return None

    def _retry_api_call(self, api_function, max_retries=3, base_delay=1):
        """帶重試機制的 API 調用"""
        for attempt in range(max_retries):
            try:
                return api_function()
            except Exception as e:
                error_str = str(e).lower()
                error_type = str(type(e).__name__).lower()
                
                # ✅ 檢查是否為額度不足錯誤
                if "insufficient_quota" in error_str or "quota" in error_str:
                    st.error("🚫 **OpenAI API 額度不足**")
                    st.error("請檢查您的 OpenAI 帳戶額度：https://platform.openai.com/usage")
                    st.info("💡 **解決方案**：\n1. 登入 OpenAI 平台\n2. 查看 Billing & Usage\n3. 增加 API 額度")
                    return None
                    
                # ✅ 檢查是否為速率限制錯誤
                elif "rate_limit" in error_str or "ratelimiterror" in error_type:
                    if attempt < max_retries - 1:  # 不是最後一次嘗試
                        delay = base_delay * (2 ** attempt)  # 指數退避
                        st.warning(f"⏳ Rate limit exceeded. Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        st.error("❌ Rate limit exceeded. Please try again later.")
                        return None
                        
                # ✅ 其他 API 錯誤
                else:
                    st.error(f"❌ **API Error**: {e}")
                    st.error("請檢查 OpenAI API Key 設定是否正確")
                    return None
        return None

    def setup_language_and_activity(self, language, activity):
        """✅ 整合新程式碼的改善：更好的活動內容處理"""
        # 檢查活動文件
        activities_dir = './activities'
        default_file = os.path.join(activities_dir, 'default.txt')
        
        # 創建 activities 目錄（如果不存在）
        if not os.path.exists(activities_dir):
            os.makedirs(activities_dir, exist_ok=True)
            
        # 如果 default.txt 不存在，創建它
        if not os.path.exists(default_file):
            try:
                with open(default_file, 'w', encoding='utf-8') as f:
                    f.write(prompts.DEFAULT_ACTIVITIY)
            except Exception as e:
                st.warning(f"Could not create default activity file: {e}")
        
        # ✅ 採用新程式碼的邏輯（您提供的改善版本）
        if os.path.isfile(os.path.join(activities_dir, activity)):
            try:
                with open(os.path.join(activities_dir, activity), 'r', encoding='utf-8') as file:
                    self.activity_content = file.read()
            except Exception as e:
                st.warning(f"Could not read activity file: {e}. Using activity as content.")
                self.activity_content = activity
        elif activity == '' or activity is None:
            try:
                with open(default_file, 'r', encoding='utf-8') as file:
                    self.activity_content = file.read()
            except Exception as e:
                st.warning(f"Could not read default activity file: {e}. Using fallback.")
                self.activity_content = prompts.DEFAULT_ACTIVITIY
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
            if input_message:  # 確保訊息不為空
                try:
                    n_inputs += len(self.tknizer.encode(str(input_message)))
                except Exception:
                    pass
        cost_input = n_inputs/1e7 * 0.15

        for output_message in output_messages:
            if output_message:  # 確保訊息不為空
                try:
                    n_outputs += len(self.tknizer.encode(str(output_message)))
                except Exception:
                    pass
        cost_output = n_outputs/1e7 * 0.6
        
        return {'cost_input': cost_input, 'cost_output': cost_output, 'ntkn_input': n_inputs, 'ntkn_output': n_outputs}

    def Chat(self, input_question, language, activity):
        """✅ 改進：加入成本控制的聊天功能"""
        
        # ✅ 加入成本控制檢查
        if 'api_usage_today' not in st.session_state:
            st.session_state.api_usage_today = 0
        
        # 每日使用限制（可調整）
        DAILY_LIMIT = 50  # 每天最多50次API調用
        
        if st.session_state.api_usage_today >= DAILY_LIMIT:
            return {
                'INPUT': {'CLS': '', 'GUIDE': '', 'EVAL': ''},
                'OUTPUT': {
                    'CLS': '3',
                    'GUIDE': f'今日API使用已達上限（{DAILY_LIMIT}次）。為了控制研究成本，請明天再繼續使用小Q，或可直接進入第4頁使用免費的ChatGPT。',
                    'EVAL': '',
                    'NEWQ': '',
                },
                'MISC': {
                    'SCAMPER_ELEMENT': '',
                    'QUESTION': input_question,
                    'cost_input': 0,
                    'cost_output': 0,
                    'ntkn_input': 0,
                    'ntkn_output': 0
                }
            }
        
        # 檢查 API 是否可用
        if not hasattr(self, 'api_available') or not self.api_available:
            return {
                'INPUT': {'CLS': '', 'GUIDE': '', 'EVAL': ''},
                'OUTPUT': {
                    'CLS': '3',
                    'GUIDE': 'API service is currently unavailable. Please check your OpenAI API configuration in Streamlit Secrets.',
                    'EVAL': '',
                    'NEWQ': '',
                },
                'MISC': {
                    'SCAMPER_ELEMENT': '',
                    'QUESTION': input_question,
                    'cost_input': 0,
                    'cost_output': 0,
                    'ntkn_input': 0,
                    'ntkn_output': 0
                }
            }
        
        if not all([activity == self.activity, language == self.language]):
            self.setup_language_and_activity(language, activity)

        output_dict = copy.deepcopy(CHAT_INFO_PLACEHOLDER)
        output_dict['MISC']['QUESTION'] = input_question

        # ✅ 分類問題（帶重試）
        cls_message = copy.deepcopy(prompts.CLS_TEMPLATE).replace('{content}', self.activity_content).replace('{question}', input_question)
        
        def classify_question():
            return self.LLM_Classifier.invoke([SystemMessage(content=cls_message)])
            
        QOutput = self._retry_api_call(classify_question)
        
        if QOutput is None:
            # API 調用失敗的備用響應
            output_dict['OUTPUT']['CLS'] = '3'
            output_dict['OUTPUT']['GUIDE'] = '💡 小Q暫時無法服務，請稍後再試。如果持續發生問題，請聯繫系統管理員檢查 API 設定。\n\n您仍可以繼續使用其他功能，或在第4頁直接與 ChatGPT 對話。'
            return output_dict
            
        # ✅ 增加使用計數
        st.session_state.api_usage_today += 1
        
        output_dict['INPUT']['CLS'] = cls_message
        output_dict['OUTPUT']['CLS'] = str(QOutput.QType)

        human_message = copy.deepcopy(prompts.USER_TEMPLATE).replace('{question}', input_question)

        # ✅ 指導型問題（帶重試）
        if QOutput.QType == 1:
            guide_message = copy.deepcopy(prompts.GUIDE_TEMPLATE).replace('{content}', self.activity_content).replace('{language}', LANGAUGE_DICT[self.language])
            
            def get_guidance():
                return self.LLM_Guidance.invoke([
                    SystemMessage(content=guide_message),
                    HumanMessage(content=human_message),
                ])
                
            output = self._retry_api_call(get_guidance)
            
            if output:
                output_dict['INPUT']['GUIDE'] = guide_message
                output_dict['OUTPUT']['GUIDE'] = output.GUID
                st.session_state.api_usage_today += 1
            else:
                output_dict['OUTPUT']['GUIDE'] = 'Service temporarily unavailable due to rate limits. Please try again later.'

        # ✅ SCAMPER型問題（帶重試）
        elif QOutput.QType == 2:
            element, examples = self.get_element()
            activity_message = copy.deepcopy(prompts.SCAMPER_TEMPLATE).replace('{content}', self.activity_content).replace('{element}', element).replace('{examples}', examples).replace('{language}', LANGAUGE_DICT[self.language])
            
            def get_scamper():
                return self.LLM_SCAMPER.invoke([
                    SystemMessage(content=activity_message),
                    HumanMessage(content=human_message),
                ])
                
            output = self._retry_api_call(get_scamper)
            
            if output:
                output_dict['INPUT']['EVAL'] = activity_message
                output_dict['OUTPUT']['EVAL'] = output.Imprv
                output_dict['OUTPUT']['NEWQ'] = output.NewQ
                output_dict['MISC']['SCAMPER_ELEMENT'] = SCAMPER_DICT[element]
                st.session_state.api_usage_today += 1
            else:
                output_dict['OUTPUT']['EVAL'] = 'Service temporarily unavailable due to rate limits. Please try again later.'
        
        # 成本計算
        input_messages = [v for k, v in output_dict['INPUT'].items() if v]
        output_messages = [v for k, v in output_dict['OUTPUT'].items() if v]
        cost_dict = self.CalculateCost(input_messages, output_messages)
        output_dict['MISC'].update(cost_dict)

        # ✅ 顯示使用狀態
        remaining = DAILY_LIMIT - st.session_state.api_usage_today
        st.sidebar.info(f"📊 今日剩餘: {remaining}/{DAILY_LIMIT} 次")

        return output_dict
