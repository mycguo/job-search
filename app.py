# UI for asking questions on the knowledge base
import streamlit as st
import os
import re
from datetime import datetime
import google.generativeai as genai
from simple_vector_store import SimpleVectorStore as MilvusVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from pages.app_admin import get_vector_store, get_text_chunks
from langchain.chains.combine_documents import create_stuff_documents_chain
import boto3
from langchain_nvidia_ai_endpoints import ChatNVIDIA


genai.configure(api_key=os.getenv("GENAI_API_KEY"))
os.environ["USER_AGENT"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

nvidia_api_key = st.secrets["NVIDIA_API_KEY"]

def get_prompt_template():
    return PromptTemplate()

def detect_remember_intent(text):
    """
    Detect if the user wants to save/remember information.
    Returns (is_remember_intent, cleaned_text)
    """
    remember_patterns = [
        r'^remember\s+that\s+(.+)',
        r'^remember\s*:\s*(.+)',
        r'^remember\s+(.+)',
        r'^save\s+this\s*:\s*(.+)',
        r'^save\s+that\s+(.+)',
        r'^store\s+this\s*:\s*(.+)',
        r'^store\s+that\s+(.+)',
        r'^keep\s+in\s+mind\s+that\s+(.+)',
        r'^note\s+that\s+(.+)',
    ]

    text_lower = text.lower().strip()

    for pattern in remember_patterns:
        match = re.match(pattern, text_lower, re.IGNORECASE)
        if match:
            # Extract the information to remember
            info = match.group(1).strip()
            return True, info

    return False, text

def enrich_information(text):
    """
    Use LLM to enrich and contextualize information before storing.
    Makes it more searchable and contextual.
    """
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

    enrichment_prompt = f"""You are helping to store information in a knowledge base.

Given the following user information, expand it slightly to make it more searchable and contextual while keeping it concise.
Add relevant context, synonyms, or related terms that might help in future searches.
Keep the core facts unchanged. Return only the enriched version.

User's information: {text}

Enriched version (2-3 sentences maximum):"""

    try:
        response = model.invoke(enrichment_prompt)
        enriched = response.content.strip()
        return enriched
    except Exception as e:
        print(f"Enrichment failed: {e}")
        return text

def save_to_knowledge_base(information, enrich=True):
    """
    Save information directly to the vector store.

    Args:
        information: The text to save
        enrich: Whether to use LLM to enrich the information

    Returns:
        tuple: (success, message)
    """
    try:
        # Optionally enrich the information
        if enrich:
            with st.spinner("Processing information..."):
                enriched_info = enrich_information(information)
        else:
            enriched_info = information

        # Add metadata
        metadata = {
            'source': 'conversational_input',
            'timestamp': datetime.now().isoformat(),
            'original': information if enrich else None
        }

        # Get vector store and add text
        vector_store = MilvusVectorStore(store_path="./vector_store_personal_assistant")
        text_chunks = get_text_chunks(enriched_info)

        # Add metadata to each chunk
        metadatas = [metadata.copy() for _ in text_chunks]
        vector_store.add_texts(text_chunks, metadatas=metadatas)

        return True, enriched_info
    except Exception as e:
        return False, str(e)

def get_chat_chain():
    prompt_template="""
    Answer the questions based on local konwledge base honestly

    Context:\n {context} \n
    Questions: \n {questions} \n

    Answers:
"""
    model=ChatGoogleGenerativeAI(model="gemini-2.5-flash",temperature=0.3)
    # This is too slow
    #model = ChatNVIDIA(
    #    model="deepseek-ai/deepseek-r1",
    #    api_key=nvidia_api_key,
    #    temperature=0.7,
    #    top_p=0.8,
    #    max_tokens=4096
    #)
    #
    prompt=PromptTemplate(template=prompt_template, input_variables=["context", "questions"], output_variables=["answers"])
    chain = create_stuff_documents_chain(llm=model, prompt=prompt, document_variable_name="context")
    return chain

def user_input(user_question):
    """
    Process user input - either save information or answer questions.
    """
    # Check if this is a "remember" command
    is_remember, extracted_info = detect_remember_intent(user_question)

    if is_remember:
        # User wants to save information
        st.info(f"💾 Saving information: '{extracted_info}'")
        success, result = save_to_knowledge_base(extracted_info, enrich=True)

        if success:
            st.success("✅ Information saved to knowledge base!")
            with st.expander("📝 What was saved (enriched version)"):
                st.write(result)
        else:
            st.error(f"❌ Failed to save: {result}")
    else:
        # Normal question answering
        vector_store = MilvusVectorStore(store_path="./vector_store_personal_assistant")
        docs = vector_store.similarity_search(user_question)

        chain = get_chat_chain()

        response = chain.invoke({"context": docs, "questions": user_question})

        print(response)
        st.write("Reply: ", response)


def download_s3_bucket(bucket_name, download_dir):
    s3 = boto3.client('s3')
    
    # Ensure the download directory exists
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    # Pagination in case the bucket has many objects
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Contents', []):
            key = obj['Key']
            local_file_path = os.path.join(download_dir, key)
            
            # Create local directories if they don't exist
            if not os.path.exists(os.path.dirname(local_file_path)):
                os.makedirs(os.path.dirname(local_file_path))
                
            print(f"Downloading {key} to {local_file_path}")
            s3.download_file(bucket_name, key, local_file_path)

def download_faiss_from_s3():
    # Milvus data is managed by the Milvus server
    # Migration from S3-stored FAISS can be done with MilvusVectorStore.migrate_from_faiss()
    print("Milvus uses its own persistence. Migration from FAISS can be done if needed.")

def main():
    st.title("AI Knowledge Assistant")
    st.header("Ask questions on your knowledge base")

    # Sidebar for manual information saving
    with st.sidebar:
        st.header("💾 Quick Save")
        st.markdown("Save information without uploading documents")

        with st.form(key="manual_save_form", clear_on_submit=True):
            info_to_save = st.text_area(
                "Information to save:",
                placeholder="Enter any information you want to remember...\nExample: My favorite color is blue",
                height=100,
                help="This will be added to your knowledge base immediately"
            )

            enrich_option = st.checkbox(
                "Enhance with AI",
                value=True,
                help="Use AI to make the information more searchable"
            )

            submit_button = st.form_submit_button("💾 Save to Knowledge Base")

            if submit_button and info_to_save.strip():
                with st.spinner("Saving information..."):
                    success, result = save_to_knowledge_base(info_to_save, enrich=enrich_option)

                if success:
                    st.success("✅ Saved successfully!")
                    if enrich_option:
                        with st.expander("📝 Enhanced version"):
                            st.write(result)
                else:
                    st.error(f"❌ Error: {result}")

        st.divider()
        st.caption("💡 **Tip**: You can also type 'Remember that...' in the chat")

    # fix the empty vector store issue
    get_vector_store(get_text_chunks("Loading some documents to build your knowledge base"))

    # Main chat interface
    st.markdown("### 💬 Chat")
    user_question = st.text_input(
        "Ask a question or say 'Remember that...' to save information:",
        placeholder="Examples: 'Tell me about Charles?' or 'Remember that I prefer Python'",
        help="Type naturally - the system will detect if you want to save or retrieve information"
    )
    if user_question:
        user_input(user_question)
    
    
    st.markdown("<div style='height:300px;'></div>", unsafe_allow_html=True)
    st.markdown(""" \n \n \n \n \n \n \n\n\n\n\n\n
        # Footnote on tech stack
        web framework: https://streamlit.io/ \n
        LLM model: "gemini-2.5-flash" \n
        Vector store: Milvus \n
        Embeddings model: Google gemini-embedding-001 \n
        LangChain: Connect LLMs for Retrieval-Augmented Generation (RAG), memory, chaining and reasoning. \n
        PyPDF2 and docx: for importing PDF and Word \n
        audio: assemblyai https://www.assemblyai.com/ \n
        Video: moviepy https://zulko.github.io/moviepy/ \n
    """)    

if __name__ == "__main__":
    main()