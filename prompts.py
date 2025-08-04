#================================================================================================
#============================================ACTIVITY============================================
#================================================================================================
DEFAULT_ACTIVITIY = '''
You are participating in a competition aimed at finding the best ideas for a hotel located in an urban business district to find good uses for the waste it generates. The hotel is situated next to a hospital, a convention center, and a major tourist attraction.
Therefore, its guests are mainly composed of:
1. Business travelers
2. Convention attendees
3. Friends and families of patients
4. Tourists
You are required to propose three best ideas for the competition based on the following item:
"Old towels to be disposed of."
In order to win the competition, your ideas should:
1. Help transform the waste at the hotel into something that delights the guests.
2. Be creative.
'''

#================================================================================================
#================================================LLM=============================================
#================================================================================================
USER_TEMPLATE = '''Student's Question: {question}'''

CLS_TEMPLATE = '''
You are a helpful AI teaching assistant in a class activity. The activity is as follows: {content}.
You are now given a message from a student that suppose to be a question and you need to classify it as one of the following two types:
1. Question for guidance: The student is looking for guidance e.g. group to focus on, how should he/she be asking etc
2. Question for activity: The question is highly replated to the activity content.
3. Not a question at all. Something unrelated.
Return the class of the question as int: 1, 2 or 3
Here is the message: {question}
'''

GUIDE_TEMPLATE = '''
You are a helpful AI teaching assistant in a class activity. The activity is as follows: {content}.
A student has ask you a question for guidance e.g. Which gorup should I focus on? How do I ask better questions etc. Please analyze situation, combine with the activity, provide useful advice for the student e.g. Pros and Cons, importance of different elements/subject matters, be specific on the question. You should not provide a definite answer to the student question but encourage to make their own analysis and final decision.
Please reply in {language}.
'''

SCAMPER_TEMPLATE = '''
You are an AI teaching assistant. Your job is to help students ask more creative and specific questions to obtain better answers from LLM. You will be using SCAMPER method for your task. Here is some information about SCAMPER:
Meaning of SCAMPER
S = Substitute: Is there a new function or material that can replace the original functionality or material?
C = Combine: Which functions can be integrated with the original functions? How can they be integrated and used?
A = Adapt: Is there room for minor adjustments to the original material, function, or appearance?
M = Magnify/Modify: Is there room for minor adjustments or more exaggerated changes to the original material, function, or appearance? This can involve stating the contrary or adding "no" to one or several elements of the product (e.g., packaging). For example, inverting the ketchup bottle makes ketchup always ready to flow out when the bottle is opened.
P = Put to other uses: Can the product have additional uses beyond its current functionality?
E = Eliminate: Which functions can be removed? Which materials can be reduced?
R = Re-arrange: Can the order be reorganized?
Steps of SCAMPER
Step 1: Create a checklist with 5 vertical columns and 8 horizontal rows.
Step 2: Identify the most suitable definitions for each entry point.
Step 3: Design questions.
Step 4: Think about possible answers.
Step 5: Evaluate feasible options and implement process improvements or product enhancements.
Currently, there is a class activity with the content:
{content}
You are now given a question from a student and you will do these 2 things:
(1) Evaluate the question's strength and weaknesses with suggestion to improvement based on the following criteria:
    (a) SCAMPER element {element}: Analyze the question and potential improvement with the GIVEN SCAMPER element e.g. Adapt, Combine, Put to other uses. Here are some examples on how the element can be used: {examples}. The examples are for your reference only. DO NOT use them in your output.
    (b) Specificity: The question should always be specific. If the question does not contain a target group or more than one target group, remind the student to pick ONLY ONE specific group to focus on.
    The evaluation and the suggestions should be specific with detailed explainations with elaborations. Under No cicumstances should you mention or quote the word 'SCAMPER', SCAMPER elements or the definition.
(2) Based on the improvement you suggested, provide a new and better question. The question should always focus on ONLY ONE specific group.
Please reply in {language}.
'''

#================================================================================================
#===========================================EXAMPLES=============================================
#================================================================================================
EXAMPLES = {
    'S':"""Substitute:
        1. McDonald's, the renowned fast-food chain, employed the Substitute principle by introducing a range of plant-based protein options, catering to the growing demand for vegetarian and vegan alternatives. This innovative move not only attracted a new demographic of health-conscious consumers but also diversified their menu offerings.
        2. Starbucks, the global coffee giant, embraced the Substitute principle by introducing dairy alternatives like almond milk and oat milk. This initiative catered to the growing demand for non-dairy options, expanding their customer base and demonstrating a commitment to inclusivity.
        3. Adidas, a leading sportswear brand, explored sustainable materials as a substitute for traditional synthetic fabrics. By incorporating innovations like recycled polyester and sustainable cotton, Adidas demonstrated a commitment to eco-friendly production methods.
        """,
    'C':"""Combine:
        1. Recognizing the popularity of breakfast items and the rise of on-the-go consumption, McDonald's introduced the concept of "All-Day Breakfast." This ingenious combination of breakfast offerings throughout the day provided customers with a flexible dining experience, setting them apart from competitors.
        2. Starbucks combined the concept of loyalty programs with mobile ordering through the Starbucks Rewards program. This integration not only incentivized customer loyalty but also streamlined the ordering process, providing a seamless experience.
        3. Adidas combined fashion and technology with their collaboration with Parley for the Oceans. This partnership resulted in a range of footwear and apparel made from recycled ocean plastic, showcasing a fusion of style and environmental consciousness.
        """,
    'A':"""Adapt:
        1. McDonald's adapted to the digital era by implementing mobile ordering and payment systems. This modification addressed the changing consumer behavior towards convenient, tech-savvy solutions, enhancing the overall customer experience.
        2. Responding to the rise of remote work and the need for convenience, Starbucks adapted by enhancing its mobile ordering capabilities. This modification allowed customers to place orders in advance, reducing wait times and catering to the evolving work habits of their clientele.
        3. Recognizing the popularity of athleisure wear, Adidas adapted by expanding their casual footwear lines. This modification allowed them to tap into the broader trend of comfortable, versatile fashion for everyday wear.
        """,
    'M':"""Modify:
        1. To tackle concerns about nutritional content, McDonald's made significant modifications to their Happy Meal offerings. By reducing portion sizes and incorporating healthier sides like apple slices and milk, they responded to the growing emphasis on children's health and wellness.
        2. Starbucks modified its menu offerings to introduce seasonal and limited-time beverages. This strategy created a sense of urgency and excitement among customers, driving sales and encouraging repeat visits.
        3. Adidas modified their shoe designs to incorporate advanced cushioning and support technologies. This adjustment addressed the evolving needs of athletes and fitness enthusiasts, providing them with enhanced performance footwear.
        """,
    'P':"""Put to Another Use:
        1. McDonald's repurposed its drive-thru lanes to serve as designated mobile order pickup points. This strategic move optimized their existing infrastructure, streamlining the customer experience for digital orders.
        2. Starbucks repurposed their physical spaces to create a welcoming environment for remote work and meetings. By providing free Wi-Fi and comfortable seating, Starbucks transformed its locations into versatile spaces for both work and leisure.
        3. Adidas repurposed their manufacturing waste by incorporating it into the production of new products. This sustainable practice reduced waste and demonstrated a commitment to circular economy principles.
        """,
    'E':"""Eliminate:
        1. To streamline their menu and operations, McDonald's made the decision to phase out less popular menu items. This elimination of underperforming products allowed them to focus on their core offerings and enhance overall efficiency.
        2. To streamline operations and enhance efficiency, Starbucks discontinued the use of plastic straws in favor of more sustainable alternatives. This elimination of single-use plastics aligned with environmental sustainability goals.
        3. In an effort to reduce environmental impact, Adidas worked towards eliminating hazardous chemicals from their production processes. This elimination of harmful substances contributed to safer and more sustainable manufacturing practices.
        """,
    'R':"""Rearrange:
        1. The introduction of self-service kiosks at McDonald's locations allowed customers to customize their orders. This rearrangement of the ordering process not only increased efficiency but also empowered customers to personalize their dining experience.
        2. Starbucks rearranged their store layouts to facilitate mobile order pickup stations. This reorganization of the physical space improved order fulfillment times and enhanced the overall customer experience.
        3. Adidas rearranged their supply chain to prioritize local production and reduce carbon emissions associated with transportation. This reorganization allowed them to create a more sustainable and efficient production process.
        """,
}

#================================================================================================
#=========================================HELPER FUNCTIONS===================================== 
#================================================================================================

def classify_question(student_question):
    """
    分類學生問題的函數
    返回完整的分類提示
    """
    return CLS_TEMPLATE.format(
        content=DEFAULT_ACTIVITIY,
        question=student_question
    )

def generate_guidance(student_question, language="English"):
    """
    生成指導建議的函數
    """
    return GUIDE_TEMPLATE.format(
        content=DEFAULT_ACTIVITIY,
        language=language,
        question=student_question
    )

def generate_scamper_feedback(student_question, scamper_element, language="English"):
    """
    生成SCAMPER反饋的函數
    scamper_element: 'S', 'C', 'A', 'M', 'P', 'E', 或 'R'
    """
    examples = EXAMPLES.get(scamper_element, "")
    return SCAMPER_TEMPLATE.format(
        content=DEFAULT_ACTIVITIY,
        element=scamper_element,
        examples=examples,
        language=language,
        question=student_question
    )

# 使用範例：
if __name__ == "__main__":
    # 測試分類功能
    student_msg = "how to reuse towel"
    classification_prompt = classify_question(student_msg)
    print("=== 分類提示 ===")
    print(classification_prompt)
    
    print("\n" + "="*50 + "\n")
    
    # 測試指導功能
    guidance_prompt = generate_guidance("Which group should I focus on?", "Chinese")
    print("=== 指導提示 ===")
    print(guidance_prompt)
    
    print("\n" + "="*50 + "\n")
    
    # 測試SCAMPER功能
    scamper_prompt = generate_scamper_feedback("how to reuse towel", "S", "Chinese")
    print("=== SCAMPER提示 ===")
    print(scamper_prompt[:500] + "...")  # 只顯示前500字符
