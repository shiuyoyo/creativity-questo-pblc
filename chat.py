import os
import copy
import random
import time
import streamlit as st
import zh_prompts

import tiktoken
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage

import prompts

LANGAUGE_DICT = {
    'E': 'english',
    'C': '繁體中文'
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

SCAMPER_DICT_ZH = {
    'S': '替代',
    'C': '結合',
    'A': '調整',
    'M': '放大／修改',
    'P': '其他用途',
    'E': '刪減',
    'R': '重組',
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
        self.tknizer = tiktoken.encoding_for_model("gpt-4o")  # 改用3.5的tokenizer
        
        # 模型配置選項
        self.model_config = {
            "standard": "gpt-4o-mini",  # 標準選項
            "premium": "gpt-4o"         # 高品質選項
        }

        # 根據環境變數或設定選擇模型，預設使用 gpt-4o-mini
        self.model_choice = os.getenv("QST_MODEL_TIER", "standard")
        self.selected_model = self.model_config.get(self.model_choice, "gpt-4o-mini")
        
        # ✅ 改進：嘗試從不同來源獲取 API Key
        api_key = self._get_api_key()
        
        if not api_key:
            st.error("⚠️ OpenAI API Key not found! Please set it in Streamlit Secrets or environment variables.")
            self.api_available = False
            return
            
        # ✅ 加入錯誤處理的 LLM 初始化 - 使用選定的模型
        try:
            st.info(f"🤖 Using model: {self.selected_model}")
            
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
        
        if 'api_usage_today' not in st.session_state:
            st.session_state.api_usage_today = 0

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
            # ✅ API 調用失敗時的智能備用響應
            output_dict['OUTPUT']['CLS'] = '2'  # 假設為活動相關問題
            
            # 提供基本的 SCAMPER 建議
            scamper_elements = ['Substitute', 'Combine', 'Adapt', 'Modify', 'Put to other uses', 'Eliminate', 'Rearrange']
            selected_element = random.choice(scamper_elements)
            
            fallback_suggestions = {
                'Substitute': '🔄 **替代思考建議**: 考慮用不同的材料或功能來替代原有的毛巾用途。例如：能否用毛巾製作其他質地的物品？',
                'Combine': '🤝 **結合思考建議**: 考慮將毛巾與其他物品或功能結合。例如：毛巾能與什麼其他飯店用品結合使用？',
                'Adapt': '🔧 **適應思考建議**: 考慮如何調整毛巾的形狀、大小或用途。例如：如何讓毛巾適合不同客群的需求？',
                'Modify': '⚡ **修改思考建議**: 考慮放大、縮小或改變毛巾的某些特性。例如：如何讓毛巾變得更有趣或實用？',
                'Put to other uses': '🎯 **新用途建議**: 考慮毛巾的全新用途。例如：除了清潔，毛巾還能為客人提供什麼價值？',
                'Eliminate': '❌ **簡化思考建議**: 考慮移除毛巾的某些元素或功能。例如：哪些部分是不必要的？',
                'Rearrange': '🔀 **重組思考建議**: 考慮重新排列毛巾的使用順序或組織方式。例如：如何改變毛巾的使用流程？'
            }
            
            suggestion = fallback_suggestions.get(selected_element, '請嘗試從不同角度思考這個問題。')
            
            output_dict['OUTPUT']['EVAL'] = f"""⚠️ **小Q目前離線中** - 但這裡有一個創意思考建議：

{suggestion}

**改進建議**: 請讓您的問題更具體化。例如：
- 專注於特定的客群（商務旅客、病患家屬等）
- 明確說明想要的物品類型
- 考慮客人的具體需求和情境

**建議的改寫問題**: "如何將廢棄毛巾轉化為對住院病患家屬有用的comfort item？"

🔧 **技術提示**: 小Q的AI服務暫時無法使用，可能是API配置問題。您可以繼續進行活動，或前往第4頁使用ChatGPT。"""
            
            output_dict['OUTPUT']['NEWQ'] = f"針對{['商務旅客', '會議參與者', '病患親友', '觀光客'][random.randint(0,3)]}，如何運用{selected_element.lower()}的概念將廢棄毛巾轉化為令人愉悅的物品？"
            output_dict['MISC']['SCAMPER_ELEMENT'] = selected_element
            
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
                output_dict['MISC']['SCAMPER_ELEMENT'] = SCAMPER_DICT[element] if self.language == 'E' else SCAMPER_DICT_ZH[element]
                st.session_state.api_usage_today += 1
            else:
                output_dict['OUTPUT']['EVAL'] = 'Service temporarily unavailable due to rate limits. Please try again later.'

        # ✅ 新增：非問題處理（來自原始repository的改進）
        elif QOutput.QType == 3:
            if self.language == 'C':
                non_question_message = """🤖 **小Q提示**: 您輸入的內容似乎不是一個問題。

為了獲得更好的協助，請嘗試：
📝 **提出具體問題**：例如「如何讓商務旅客更滿意？」
🎯 **聚焦特定目標**：選擇一個客群進行深入思考
💡 **尋求建議**：詢問改進創意的方法

**範例問題**：「針對病患家屬，廢棄毛巾可以如何轉化為實用的物品？」"""
            else:
                non_question_message = """🤖 **Little Q Notice**: Your input doesn't seem to be a question.

For better assistance, please try:
📝 **Ask specific questions**: e.g., "How to better satisfy business travelers?"
🎯 **Focus on specific targets**: Choose one customer group for deeper thinking
💡 **Seek advice**: Ask for methods to improve creativity

**Example question**: "For patient families, how can discarded towels be transformed into practical items?" """
            
            output_dict['OUTPUT']['GUIDE'] = non_question_message
        
        # 成本計算
        input_messages = [v for k, v in output_dict['INPUT'].items() if v]
        output_messages = [v for k, v in output_dict['OUTPUT'].items() if v]
        cost_dict = self.CalculateCost(input_messages, output_messages)
        output_dict['MISC'].update(cost_dict)

        # 顯示使用狀態
        st.sidebar.info(f"📊 今日已使用: {st.session_state.api_usage_today} 次")

        return output_dict
