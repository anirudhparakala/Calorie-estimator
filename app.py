import streamlit as st
import requests
import base64
import json
from PIL import Image
import io

# --- Page Configuration ---
st.set_page_config(
    page_title="Intelligent AI Calorie Estimator",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Gemini API Configuration ---
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

    # --- Session State Initialization ---
    if "analysis_stage" not in st.session_state:
        st.session_state.analysis_stage = "upload"
    if "uploaded_image_data" not in st.session_state:
        st.session_state.uploaded_image_data = None
    if "api_response" not in st.session_state:
        st.session_state.api_response = {}

    # --- Step 1: Image Upload ---
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

    # --- Step 2: Display Image and Analyze Button ---
    if st.session_state.analysis_stage == "analyzing":
        st.image(st.session_state.uploaded_image_data, caption="Your uploaded meal.", use_container_width=True)
        if st.button(" Analyze Food"):
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
                - First, identify the overall dish or meal type. This provides top-level context.
                - Then, perform a component inventory, listing every single distinct food item.

                **Step 2: Evidence-Based Analysis (Internal Deduction)**
                - For each item, perform a mental check for Quantity, Preparation, and Deduction.
                - Default to **"medium" confidence** for complex, multi-ingredient dishes.
                - **Calorie Attribution Rule:** When a dish is "pan-fried" or "deep-fried," you MUST attribute the majority of added calories to **Fat** and/or **Carbs** (from breading), not Protein.

                **Step 3: Knowledge Gap Identification & Question Formulation**
                - Build your "question queue" based on the following priorities:

                    - **1. Deconstructive Questioning (Top Priority):** For a composite item (smoothie, fritters), first ask if the user can provide the raw ingredient quantities. To enable a follow-up text box, you **MUST** include a `"follow_up_prompt"` key in the question object.
                    - **2. Quantity Check:** If not covered by the above and confidence is not "high", ask to clarify the portion size. You are **FORBIDDEN** from asking about quantity for "high" confidence items.
                    - **3. Critical Non-Visual Check:** Ask about Preparation & Fats, Ingredient Specification (fat %), and Origin.
                    - **4. Question Review:** Ensure each question is a single, distinct query.

                ---

                ##  Exemplars of Perfect Execution (Learn from these)
                Before you execute, study these examples. Replicate their logic and output format precisely.

                **--- EXAMPLE 1: Simple Case (No questions needed) ---**
                * **User Uploads:** A photo of a single, whole apple.
                * **Your Perfect Output:**
                    ```json
                    {
                      "estimations": [{"item": "Red Apple", "amount": "1 medium", "confidence_score": "high"}],
                      "questions": []
                    }
                    ```

                **--- EXAMPLE 2: Deconstructive Question Case ---**
                * **User Uploads:** A photo of a homemade smoothie.
                * **Your Perfect Output:**
                    ```json
                    {
                      "estimations": [{"item": "Fruit Smoothie", "amount": "Approximately 12 oz", "confidence_score": "low"}],
                      "questions": [
                        {
                          "id": "q1",
                          "text": "To get the most accurate estimate, do you happen to know the individual ingredients used in this smoothie?",
                          "options": ["Yes, I can provide the details", "No, please estimate visually"],
                          "follow_up_prompt": "Great! Please list the ingredients and their amounts (e.g., 1 banana, 1/2 cup milk, 1 scoop protein powder):"
                        }
                      ]
                    }
                    ```
                **--- EXAMPLE 2: Deconstructive Question Case ---**
                * **User Uploads:** A photo of a homemade smoothie.
                * **Your Perfect Output:**
                ```json
                {
                  "estimations": [
                  { "item": "Dal Makhani", "amount": "Approximately 1 cup", "confidence_score": "medium" },
                  { "item": "Plain White Rice", "amount": "Approximately 1 cup", "confidence_score": "high" },
                  { "item": "Gulab Jamun", "amount": "1 piece", "confidence_score": "high" },
                  { "item": "Aloo Sabzi (Potato Curry)", "amount": "Approximately 1/2 cup", "confidence_score": "medium" },
                  { "item": "Roti", "amount": "2 pieces", "confidence_score": "high" }
                    ],
                 "questions": [
                   {
                      "id": "q1",
                      "text": "What type of oil or fat was used in preparing the dishes?",
                      "options": ["Ghee", "Vegetable Oil", "Butter", "Other"]
                   },
                   {
                     "id": "q2",
                     "text": "Were these dishes homemade or from a restaurant?",
                     "options": ["Homemade", "Restaurant"]
                   }
                 ]
                }
                 ```
                ---

                ##  OUTPUT SPECIFICATION (API CONTRACT)

                Analyze the user's image that follows. You MUST return your findings in a single, valid JSON object. No additional text.
                The `estimations` and `questions` keys MUST have a LIST of objects as their value.
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

        if not isinstance(estimations, list): estimations = []
        if not isinstance(questions, list): questions = []
        valid_questions = [q for q in questions if isinstance(q, dict) and 'id' in q]

        if not estimations and not valid_questions:
            st.error("The AI was unable to analyze this image. Please try again with a different photo.", icon="🤷")
            if st.button("Start Over with a New Image"):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()
        else:
            st.subheader("AI's Initial Analysis:", divider='rainbow')
            if estimations:
                for est in estimations:
                    if isinstance(est, dict):
                        st.success(f"**{est.get('item', 'N/A')}:** Estimated as **{est.get('amount', 'N/A')}**",
                                   icon="✅")

            st.write("---")

            if not valid_questions:
                st.success("The AI is highly confident and has no further questions!")
                if st.button(" Calculate Final Estimate Now"):
                    st.session_state.user_answers = {}
                    st.session_state.analysis_stage = "calculating_final"
                    st.rerun()
            else:
                st.subheader("Please answer the remaining questions:", divider='rainbow')
                user_answers = {}
                for q in valid_questions:
                    question_text = q.get('text', 'Please provide details:')
                    if q.get("options") and isinstance(q["options"], list) and len(q["options"]) > 0:
                        options_list = q["options"]
                        selected_option = st.radio(label=question_text, options=options_list, key=q['id'])

                        show_text_input = False
                        follow_up_label = "Please provide the details:"

                        if q.get("follow_up_prompt") and selected_option == options_list[0]:
                            show_text_input = True
                            follow_up_label = q.get("follow_up_prompt")
                        elif "please specify" in selected_option.lower():
                            show_text_input = True
                            follow_up_label = f"Please specify for '{selected_option}':"
                        elif "yes" in selected_option.lower():
                            show_text_input = True

                        if show_text_input:
                            specification_text = st.text_area(label=follow_up_label, key=f"{q['id']}_specify")
                            user_answers[q['id']] = f"{selected_option}: {specification_text}"
                        else:
                            user_answers[q['id']] = selected_option
                    else:
                        user_answers[q['id']] = st.text_input(label=question_text, key=q['id'])

                if st.button(" Submit Answers and Get Estimate"):
                    st.session_state.user_answers = user_answers
                    st.session_state.analysis_stage = "calculating_final"
                    st.rerun()

    if st.session_state.analysis_stage == "calculating_final":
        with st.spinner("Calculating final estimate... "):
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

            Based on ALL of this information combined, your task is twofold:
            1.  Provide a nutritional breakdown for EACH food item. Return this as a valid JSON object with a single key, "breakdown". Each object in the list must have keys for "item", "calories", "protein_grams", "carbs_grams", and "fat_grams". Estimate numerical values and adjust them based on the user's answers.
            2.  After the JSON, on a new line, add the separator "---". Then, write a brief, one or two-sentence summary of the meal. In this summary, **DO NOT** mention any total calorie numbers or ranges.
            """

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
            calories, protein, carbs, fat = item.get("calories", 0), item.get("protein_grams", 0), item.get(
                "carbs_grams", 0), item.get("fat_grams", 0)
            total_calories, total_protein, total_carbs, total_fat = total_calories + calories, total_protein + protein, total_carbs + carbs, total_fat + fat
            display_data.append(
                {"Item": item.get("item", "N/A"), "Calories": f"{calories} kcal", "Protein": f"{protein}g",
                 "Carbs": f"{carbs}g", "Fat": f"{fat}g"})

        st.table(display_data)

        st.subheader("Calculated Totals", divider='rainbow')
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Calories", f"{total_calories} kcal")
        col2.metric("Total Protein", f"{total_protein}g")
        col3.metric("Total Carbs", f"{total_carbs}g")
        col4.metric("Total Fat", f"{total_fat}g")

        if st.button("Start Over with a New Image"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()


def call_gemini_api(prompt_text, image_b64):
    if not GEMINI_API_KEY:
        st.error("Gemini API Key is not configured.")
        return None
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [
        {"parts": [{"text": prompt_text}, {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}}]}],
               "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4096}}
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload), timeout=90)
        response.raise_for_status()
        full_response_json = response.json()
        response_text = full_response_json['candidates'][0]['content']['parts'][0]['text']
        try:
            parts = response_text.split('---', 1)
            json_str = parts[0]
            summary_text = parts[1].strip() if len(parts) > 1 else "No summary provided."
            start_index = json_str.find('{');
            end_index = json_str.rfind('}') + 1
            json_str_cleaned = json_str[start_index:end_index]
            parsed_json = json.loads(json_str_cleaned);
            parsed_json['summary_text'] = summary_text
            return parsed_json
        except (json.JSONDecodeError, IndexError):
            try:
                start_index = response_text.find('{');
                end_index = response_text.rfind('}') + 1
                json_str = response_text[start_index:end_index]
                return json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                return {"text": response_text}
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}"); return None
    except (KeyError, IndexError) as e:
        st.error(f"Error: Could not parse API response. Error: {e}");
        st.write("Raw API Response for debugging:");
        st.json(full_response_json)
        return None


if __name__ == "__main__":
    main()