import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import json
from fpdf import FPDF
import io

# 1. Page Configuration
st.set_page_config(page_title="Free AI Study Suite", page_icon="🎓", layout="wide")
st.title("🎓 Free AI Ultimate Study Suite Prototype")
st.write("A completely free prototype to test features before our charity-backed launch!")

# 2. Setup the Free Tier API Guardrail
st.sidebar.header("🔑 Setup")
api_key = st.sidebar.text_input("Enter your free Gemini API Key to test:", type="password")
st.sidebar.markdown("[Get a free API key here](https://google.com)")

if not api_key:
    st.info("💡 Drop a Gemini API Key in the sidebar to unlock all the prototype study tools!")
else:
    # Initialize the AI Client
    client = genai.Client(api_key=api_key)

    # 3. Create the 4 Functional Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚡ Multimodal Flashcard Maker",
        "🤖 Homework Coach (Vision)", 
        "✍️ Essay Checker", 
        "📄 Test PDF Generator"
    ])

    # ==========================================
    # TAB 1: MULTIMODAL FLASHCARD MAKER (PDF / IMAGE)
    # ==========================================
    with tab1:
        st.header("⚡ Upload Notes ➡️ Get Flashcards")
        st.write("Upload a PDF document, worksheet, or a photo of your handwritten notes to generate a custom deck!")

        # File uploader that supports images and PDFs directly
        uploaded_study_file = st.file_uploader(
            "Upload your study material:", 
            type=["pdf", "jpg", "jpeg", "png"], 
            key="fc_multimodal_uploader"
        )
        
        card_count = st.slider("Number of cards to make:", min_value=3, max_value=10, value=5, key="fc_count")

        if st.button("🚀 Build Flashcard Deck from File", key="fc_btn"):
            if not uploaded_study_file:
                st.warning("Please upload a file or photo first!")
            else:
                with st.spinner("Reading your file and synthesizing custom flashcards..."):
                    card_prompt = f"Create exactly {card_count} study flashcards based directly on the attached material. Extract the most important formulas, terms, or concepts."
                    
                    # Prepare the multimodal inputs array
                    ai_inputs = [card_prompt]
                    file_type = uploaded_study_file.type
                    
                    try:
                        # Process based on file type
                        if "pdf" in file_type:
                            pdf_bytes = uploaded_study_file.read()
                            ai_inputs.append(
                                types.Part.from_bytes(
                                    data=pdf_bytes,
                                    mime_type="application/pdf"
                                )
                            )
                        else:
                            img = Image.open(uploaded_study_file)
                            ai_inputs.append(img)
                            
                        # UPDATED MODEL TO GEMINI-3.6-FLASH
                        response = client.models.generate_content(
                            model='gemini-3.6-flash', 
                            contents=ai_inputs,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema={
                                    "type": "ARRAY",
                                    "items": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "question": {"type": "STRING"},
                                            "answer": {"type": "STRING"}
                                        },
                                        "required": ["question", "answer"]
                                    }
                                }
                            )
                        )
                        
                        st.session_state['app_deck'] = json.loads(response.text)
                        st.session_state['app_deck_index'] = 0
                        st.success("Deck created successfully from your file!")
                    except Exception as e:
                        st.error(f"Failed to generate flashcards. Error details: {e}")

        # Render active cards
        if 'app_deck' in st.session_state and st.session_state['app_deck']:
            current_deck = st.session_state['app_deck']
            current_idx = st.session_state['app_deck_index']
            active_card = current_deck[current_idx]
            
            st.write(f"Card {current_idx + 1} of {len(current_deck)}")
            with st.container(border=True):
                st.markdown(f"### ❓ **Question:**\n{active_card['question']}")
                with st.expander("👁️ Reveal Answer"):
                    st.markdown(f"### ✨ **Answer:**\n{active_card['answer']}")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("⏮️ Back", key="fc_back") and current_idx > 0:
                    st.session_state['app_deck_index'] -= 1
                    st.rerun()
            with c2:
                if st.button("Next ⏭️", key="fc_next") and current_idx < len(current_deck) - 1:
                    st.session_state['app_deck_index'] += 1
                    st.rerun()

    # ==========================================
    # TAB 2: HOMEWORK COACH (VISION)
    # ==========================================
    with tab2:
        st.header("📸 AI Homework Coach")
        st.write("Upload a photo of a problem. The AI coaches you without giving away the direct answers!")

        uploaded_file = st.file_uploader("Upload problem image", type=["jpg", "jpeg", "png"], key="problem_upload")
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Your Uploaded Homework", width=400)
            
            if st.button("🧠 Ask Coach for Help", key="coach_help_btn"):
                with st.spinner("Analyzing problem..."):
                    tutor_prompt = """
                    You are an encouraging academic tutor. Look at this image. 
                    CRITICAL: Do NOT give the final answer under any circumstances. 
                    Instead, identify the core concept and provide a 'Step 1' hint to help the user solve it.
                    """
                    try:
                        # UPDATED MODEL TO GEMINI-3.6-FLASH
                        response = client.models.generate_content(model='gemini-3.6-flash', contents=[image, tutor_prompt])
                        st.subheader("💡 Coach's Guidance:")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"Error: {e}")

            st.divider()
            st.subheader("✅ Submit Your Attempted Solution")
            user_text_attempt = st.text_area("Type your solution steps here:", key="coach_attempt_text")
            
            if st.button("📝 Verify My Answer", key="coach_verify_btn"):
                if user_text_attempt:
                    with st.spinner("Checking logic..."):
                        verify_prompt = f"""
                        The student is working on the image problem. They attempted this solution: '{user_text_attempt}'.
                        1. State clearly if they are correct. 
                        2. Explain WHY their logic works, or gently guide them if they made a mistake.
                        """
                        try:
                            # UPDATED MODEL TO GEMINI-3.6-FLASH
                            response = client.models.generate_content(model='gemini-3.6-flash', contents=[image, verify_prompt])
                            st.subheader("📋 Coach's Feedback:")
                            st.write(response.text)
                        except Exception as e:
                            st.error(f"Error: {e}")

    # ==========================================
    # TAB 3: ESSAY GRAMMAR CHECKER
    # ==========================================
    with tab3:
        st.header("✍️ Essay Grammar & Style Checker")
        st.write("Paste your text (up to 3,000 words) to receive professional, formatted editing feedback.")

        user_essay = st.text_area("Paste your essay text here:", height=250, placeholder="Type or paste your essay...", key="essay_text")

        if user_essay:
            word_count = len(user_essay.split())
            st.info(f"📊 Current Word Count: {word_count} / 3,000 words")

            if word_count > 3000:
                st.error("❌ Your essay exceeds the 3,000-word limit.")
            else:
                if st.button("🔍 Analyze Essay", key="essay_btn"):
                    with st.spinner("Reviewing your writing..."):
                        essay_prompt = f"Act as an English professor. Review this essay for a grade, specific grammar corrections, and style tips:\n\n'{user_essay}'"
                        try:
                            # UPDATED MODEL TO GEMINI-3.6-FLASH
                            response = client.models.generate_content(model='gemini-3.6-flash', contents=essay_prompt)
                            st.subheader("📋 Professor Feedback Report")
                            st.write(response.text)
                        except Exception as e:
                            st.error(f"Error: {e}")

    # ==========================================
    # TAB 4: PRACTICE TEST PDF GENERATOR
    # ==========================================
    with tab4:
        st.header("📄 Custom Practice Test Generator")
        st.write("Generate a customized practice exam and download it as a printable PDF.")

