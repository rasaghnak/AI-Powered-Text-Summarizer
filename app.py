import streamlit as st
from transformers import PegasusForConditionalGeneration, PegasusTokenizer
from concurrent.futures import ThreadPoolExecutor

# Load Pegasus Model
@st.cache_resource
def load_summarization_models():
    pegasus_model = PegasusForConditionalGeneration.from_pretrained("google/pegasus-large")
    pegasus_tokenizer = PegasusTokenizer.from_pretrained("google/pegasus-large")
    return pegasus_model, pegasus_tokenizer

pegasus_model, pegasus_tokenizer = load_summarization_models()

# Chunking Text
def split_text_into_chunks(text, max_chunk_size=2048):
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

# Summarize Each Chunk
def summarize_chunk(chunk, model, tokenizer):
    inputs = tokenizer.encode("summarize: " + chunk, return_tensors="pt", max_length=2048, truncation=True)
    outputs = model.generate(inputs, max_length=500, min_length=100, num_beams=5, early_stopping=True)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Hierarchical Summarization
def hierarchical_summarization(input_text, model, tokenizer):
    # Step 1: Split into chunks
    chunks = split_text_into_chunks(input_text, max_chunk_size=2048)
    
    # Step 2: Summarize each chunk in parallel
    with ThreadPoolExecutor() as executor:
        chunk_summaries = list(executor.map(lambda chunk: summarize_chunk(chunk, model, tokenizer), chunks))
    
    # Step 3: Combine chunk summaries into a cohesive text
    combined_text = " ".join(chunk_summaries)
    
    # Step 4: Generate the final detailed summary
    final_summary = summarize_chunk(combined_text, model, tokenizer)
    
    return final_summary

# Streamlit UI
st.title("Enhanced Text Summarization Tool")
st.write("Upload large documents or enter text to generate detailed and high-quality summaries.")

# Input Section
uploaded_file = st.file_uploader("Upload a text file", type=["txt"])
input_text = st.text_area("Or enter text manually")

if uploaded_file:
    input_text = uploaded_file.read().decode("utf-8")

if input_text:
    st.subheader("Input Text")
    st.write(input_text)

    # Summarization
    with st.spinner("Summarizing..."):
        final_summary = hierarchical_summarization(input_text, pegasus_model, pegasus_tokenizer)
    
    st.subheader("Generated Summary")
    st.write(final_summary)
 