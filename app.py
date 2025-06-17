import streamlit as st
import requests
import base64
import json
from PIL import Image
import io

st.set_page_config(
    page_title="Intelligent AI Calorie Estimator",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="auto"
)

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    st.warning("GEMINI_API_KEY not found in secrets. Please enter it below to run locally.", icon="⚠️")
    GEMINI_API_KEY = st.text_input("Enter your Gemini API Key:", type="password")

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}"

def load_css():
    st.markdown("""
        <style>
            .stButton>button {
                border-radius: 20px;
                padding: 10px 20px;
                font-weight: bold;
                border: 2px solid #4F8BF9;
                background-color: transparent;
            }
            .stButton>button:hover {
                border-color: #0B5ED7;
                color: #0B5ED7;
            }
        </style>
    """, unsafe_allow_html=True)


def main():
    load_css()

    st.title("Intelligent AI Calorie Estimator 🧠")
    st.info("Upload a food photo. The AI will estimate what it can and only ask what it needs to.", icon="🧑‍🔬")

    if "analysis_stage" not in st.session_state:
        st.session_state.analysis_stage = "upload"
    if "uploaded_image_data" not in st.session_state:
        st.session_state.uploaded_image_data = None
    if "api_response" not in st.session_state:
        st.session_state.api_response = {}

    if st.session_state.analysis_stage == "upload":
        uploaded_file = st.file_uploader(
            "Upload an image of your meal...",
            type=["jpg", "jpeg", "png"],
            help="Take a clear, well-lit photo of your food for the best results."
        )
        if uploaded_file:
            st.session_state.uploaded_image_data = uploaded_file.getvalue()
            st.session_state.analysis_stage = "analyzing"
            st.rerun()

    if st.session_state.analysis_stage == "analyzing":
        st.image(st.session_state.uploaded_image_data, caption="Your uploaded meal.", use_container_width=True)
        if st.button("🔬 Analyze Food"):
            with st.spinner("Performing advanced analysis... Please wait."):

                prompt = """
                // SYSTEM IDENTITY
                You are "Nutri-AI v2.0," an advanced nutritional analysis agent powered by the Gemini 1.5 Pro model.
                Your Core Directive is to convert visual food data into structured nutritional insights with maximum accuracy and minimal user friction.
                Your Guiding Principle is: **Precision over Assumption. Inquiry over Ignorance.**

                ---

                // COGNITIVE WORKFLOW: CHAIN OF THOUGHT (CoT)
                // You MUST follow this multi-step reasoning process internally before generating the final output.

                **Step 1: Scene Deconstruction & Holistic Recognition**
                - First, identify the overall dish or meal type (e.g., "Classic American Cheeseburger," "North Indian Thali," "Fruit Smoothie"). This provides top-level context.
                - Then, perform a component inventory, listing every single distinct food item you can visually identify.

                **Step 2: Evidence-Based Analysis (Internal Deduction)**
                - For each item in your inventory, execute the following internal analysis:
                    - **Visual Quantity Estimation:** Scrutinize the image for scale references (cutlery, hands, dishware). Estimate the volume/weight.
                    - **Visual Preparation Analysis:** Look for tell-tale visual cues: char marks (grilling), uniform golden crust (deep frying), oil sheen (pan-frying), lack of browning (steaming/boiling).
                    - **Confidence Assignment:** Based on the quality of visual evidence, assign a `confidence_score` ("high", "medium", or "low") to your quantity estimation for that item. Default to "medium" for complex, mixed dishes like stews or casseroles.

                **Step 3: Knowledge Gap Identification & Question Formulation**
                     - After your internal analysis, identify what critical information is impossible to know visually and build your "question queue" based on the following priorities:

                      - **1. Deconstructive Questioning (Top Priority):** If you identify a composite item (like fritters, meatballs, patties, kebabs, or nuggets), your first and most important question should be about the quantity of the raw, primary ingredient. Frame this as an optional, expert question.
                      - **To do this, include a `"follow_up_on"` key in your question object.** The value of this key should be the exact option text that triggers a text input box for the user to specify details.
                      - **Example:**
                        ```json
                         {
                           "id": "q1",
                            "text": "To get the most accurate estimate, do you happen to know the individual ingredients used in this smoothie?",
                            "options": ["Yes, I can list them", "No, please estimate visually"],
                            "follow_up_on": "Yes, I can list them"
                         }
                        ```
                      - *Example:* For chicken fritters, ask: "To get the most accurate estimate, do you happen to know how much raw chicken was used?" with options like `["Yes, about 250g / 0.5 lbs", "Yes, about 500g / 1 lb", "No, please estimate visually"]`.

                      - **2. Quantity Check:** If you have NOT asked a deconstructive question for an item, AND its quantity confidence is "medium" or "low," you MUST prepare a clarifying multiple-choice question about its portion size. If confidence is "high," you are FORBIDDEN from asking about quantity.

                      - **3. Critical Non-Visual Check:** Prepare questions for high-impact, non-visual data. Your priorities are:
                     - **Preparation & Fats:** How was it cooked and with what kind of fat/oil?
                     - **Ingredient Specification:** If relevant, what is the meat's fat % or the dairy's fat content?
                     - **Origin:** Was the meal homemade or from a restaurant?

                     - **4. Question Review:** Finally, ensure each generated question is a single, distinct query. Do not merge multiple topics into one sentence.

                **Step 4: Output Assembly**
                - After completing the full reasoning chain, assemble your findings into the strictly-defined JSON format below. Your internal monologue is for your process only and MUST NOT be in the final output.

                ---

                // OUTPUT SPECIFICATION (API CONTRACT)
                // Your entire output MUST be a single, valid JSON object and nothing else.

                **JSON Schema:**
                {
                  "estimations": [
                    {
                      "item": "string",
                      "amount": "string",
                      "confidence_score": "string" // "high", "medium", or "low"
                    }
                  ],
                  "questions": [
                    {
                      "id": "string", // e.g., "q1", "q2"
                      "text": "string",
                      "options": ["string", "string", ...] // Optional, for multiple choice
                    }
                  ]
                }

                **Reference Implementation:**
                * **User Uploads:** A photo of a large hamburger on a plate.
                * **Your Perfect JSON Output:**
                    ```json
                    {
                      "estimations": [
                        { "item": "Beef Patty", "amount": "Approximately 1/3 lb (6 oz)", "confidence_score": "medium" },
                        { "item": "Brioche Bun", "amount": "1 set", "confidence_score": "high" },
                        { "item": "Cheddar Cheese", "amount": "1 slice", "confidence_score": "high" }
                      ],
                      "questions": [
                        { "id": "q1", "text": "The beef patty looks to be around 1/3 lb. Is that accurate?", "options": ["Yes, about that size", "No, it's smaller (approx 1/4 lb)", "No, it's larger (approx 1/2 lb)"] },
                        { "id": "q2", "text": "What is the approximate lean/fat percentage of the beef?", "options": ["Lean (90/10 or leaner)", "Standard (80/20)", "I'm not sure"] },
                        { "id": "q3", "text": "Was this burger homemade or from a restaurant?", "options": ["Homemade", "A Fast-Food Chain", "A Sit-down Restaurant"] }
                      ]
                    }
                    ```

                ---

                // EXECUTION DIRECTIVE
                Initiate Cognitive Workflow for the following user-provided image. Adhere strictly to all protocols. Provide ONLY the final JSON output.
                """

                image_b64 = base64.b64encode(st.session_state.uploaded_image_data).decode()
                response_json = call_gemini_api(prompt, image_b64)

                if response_json:
                    st.session_state.api_response = response_json
                    st.session_state.analysis_stage = "review_and_answer"
                    st.rerun()
                else:
                    st.error("The AI could not analyze the image. Please try another one.")

    if st.session_state.analysis_stage == "review_and_answer":
        estimations = st.session_state.api_response.get("estimations", [])
        questions = st.session_state.api_response.get("questions", [])

        if not isinstance(estimations, list):
            estimations = []
        if not isinstance(questions, list):
            questions = []

        valid_questions = [q for q in questions if isinstance(q, dict) and 'id' in q]

        if not estimations and not valid_questions:
            st.error(
                "The AI was unable to analyze this image. This can happen with very abstract, unclear, or non-food images. Please try again with a different photo.",
                icon="🤷")
            if st.button("Start Over with a New Image"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        else:
            st.subheader("AI's Initial Analysis:", divider='rainbow')
            if not estimations:
                st.warning("The AI could not make any initial estimations and needs your help with all items.")
            else:
                for est in estimations:
                    if isinstance(est, dict):
                        item_name = est.get('item', 'Unknown Item')
                        item_amount = est.get('amount', 'N/A')
                        st.success(f"**{item_name}:** Estimated as **{item_amount}**", icon="✅")
                    else:
                        st.warning(f"AI provided an estimation in an unexpected format: {est}")

            st.write("---")

            if not valid_questions:
                st.success("The AI is highly confident and has no further questions!")
                if st.button("✅ Calculate Final Estimate Now"):
                    st.session_state.user_answers = {}
                    st.session_state.analysis_stage = "calculating_final"
                    st.rerun()
            else:
                st.subheader("Please answer the remaining questions:", divider='rainbow')
                user_answers = {}
                for q in valid_questions:
                    question_text = q.get('text', 'Please provide details:')
                    if q.get("options") and isinstance(q["options"], list) and len(q["options"]) > 0:
                        selected_option = st.radio(label=question_text, options=q['options'], key=q['id'])
                        if "please specify" in selected_option.lower():
                            specification_text = st.text_input(label=f"Please specify for '{selected_option}'",
                                                               key=f"{q['id']}_specify")
                            user_answers[q['id']] = f"{selected_option}: {specification_text}"
                        else:
                            user_answers[q['id']] = selected_option
                    else:
                        user_answers[q['id']] = st.text_input(label=question_text, key=q['id'])
                if st.button("✅ Submit Answers and Get Estimate"):
                    st.session_state.user_answers = user_answers
                    st.session_state.analysis_stage = "calculating_final"
                    st.rerun()

    if st.session_state.analysis_stage == "calculating_final":
        with st.spinner("Calculating final estimate... 🤌"):
            image_b64 = base64.b64encode(st.session_state.uploaded_image_data).decode()

            estimations_list = st.session_state.api_response.get("estimations", [])
            questions_list = st.session_state.api_response.get("questions", [])

            estimations_str = "\n".join(
                [f"- {est.get('item', 'N/A')}: {est.get('amount', 'N/A')}" for est in estimations_list if
                 isinstance(est, dict)])
            answers_str = "\n".join([
                                        f"- For '{q.get('text', 'a question')}', user answered: '{st.session_state.user_answers.get(q.get('id'), 'No answer')}'"
                                        for q in questions_list if isinstance(q, dict)])

            final_prompt = f"""
            You are a nutritionist performing a final, detailed analysis. You have already analyzed an image and received user feedback.
            **Your Initial Estimations:**
            {estimations_str}
            **User's Answers to Your Questions:**
            {answers_str}

            Your task is twofold:

1.  **Generate a Detailed Breakdown:** Based on ALL available information, provide a nutritional breakdown for EACH food item.
    - **CRITICAL:** You MUST adjust the nutritional values in the breakdown to reflect the user's answers, especially for portion sizes or serving counts. For example, if the user confirmed "two servings" of an item, the corresponding "calories", "protein_grams", etc., in your breakdown for that item should be for **both servings combined**.
    - Return this as a valid JSON object with a single key, "breakdown".

2.  **Write a Qualitative Summary:** After the JSON, on a new line, add the separator "---". Then, write a brief, one or two-sentence summary providing qualitative insights about the meal's composition (e.g., "This meal is high in protein from the chicken," or "The use of ghee contributes significantly to the fat content.").
    - **DO NOT** mention any total calorie numbers or ranges in this text summary. The app will calculate the totals itself.

Example Format for your entire output:
```json
{{
  "breakdown": [
    {{
      "item": "Chicken Biryani (2 servings)",
      "calories": 800,
      "protein_grams": 60,
      "carbs_grams": 100,
      "fat_grams": 30
    }},
    {{
      "item": "Raita (1/4 cup)",
      "calories": 30,
      "protein_grams": 2,
      "carbs_grams": 5,
      "fat_grams": 1
    }}
  ]
}}
---
This biryani is a protein-rich meal. The use of ghee, as confirmed, adds significantly to the overall fat content. """

            final_response_json = call_gemini_api(final_prompt, image_b64)

            if final_response_json and "breakdown" in final_response_json:
                st.session_state.final_breakdown = final_response_json
                st.session_state.analysis_stage = "results"
                st.rerun()
            else:
                st.error("The AI could not generate a final breakdown. Please try again.")
                st.session_state.analysis_stage = "review_and_answer"

    if st.session_state.analysis_stage == "results":
        st.success("### Here is your detailed nutritional estimate:", icon="🎉")

        breakdown_data = st.session_state.get("final_breakdown", {})
        breakdown_list = breakdown_data.get("breakdown", [])
        summary_text = breakdown_data.get("summary_text", "No summary provided.")

        st.markdown(summary_text)
        st.write("---")

        total_calories, total_protein, total_carbs, total_fat = 0, 0, 0, 0
        display_data = []

        for item in breakdown_list:
            calories = item.get("calories", 0)
            protein = item.get("protein_grams", 0)
            carbs = item.get("carbs_grams", 0)
            fat = item.get("fat_grams", 0)

            total_calories += calories
            total_protein += protein
            total_carbs += carbs
            total_fat += fat

            display_data.append({
                "Item": item.get("item", "N/A"),
                "Calories": f"{calories} kcal",
                "Protein": f"{protein}g",
                "Carbs": f"{carbs}g",
                "Fat": f"{fat}g"
            })

        st.table(display_data)

        st.subheader("Calculated Totals", divider='rainbow')
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Calories", f"{total_calories} kcal")
        col2.metric("Total Protein", f"{total_protein}g")
        col3.metric("Total Carbs", f"{total_carbs}g")
        col4.metric("Total Fat", f"{total_fat}g")

        if st.button("Start Over with a New Image"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def call_gemini_api(prompt_text, image_b64):
    if not GEMINI_API_KEY:
        st.error("Gemini API Key is not configured.")
        return None

    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [
            {"parts": [{"text": prompt_text}, {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4096},
    }

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload), timeout=90)
        response.raise_for_status()
        full_response_json = response.json()
        response_text = full_response_json['candidates'][0]['content']['parts'][0]['text']

        try:
            parts = response_text.split('---', 1)
            json_str = parts[0]
            summary_text = parts[1].strip() if len(parts) > 1 else "No summary provided."

            start_index = json_str.find('{')
            end_index = json_str.rfind('}') + 1
            json_str_cleaned = json_str[start_index:end_index]

            parsed_json = json.loads(json_str_cleaned)
            parsed_json['summary_text'] = summary_text
            return parsed_json

        except (json.JSONDecodeError, IndexError):
            try:
                start_index = response_text.find('{')
                end_index = response_text.rfind('}') + 1
                json_str = response_text[start_index:end_index]
                return json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                return {"text": response_text}

    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None
    except (KeyError, IndexError) as e:
        st.error(f"Error: Could not parse the API response. The format may be unexpected. Error: {e}")
        st.write("Raw API Response for debugging:")
        st.json(full_response_json)
        return None


if __name__ == "__main__":
    main()