import streamlit as st
import pandas as pd
import io
from openai import OpenAI

st.set_page_config(page_title="AI Data Assistant", layout="wide")

st.title("🤖 AI Data Processing Assistant")
st.markdown("Upload your Excel/CSV file, describe what you need in plain English, and let AI handle the rest.")
st.caption("💡 Powered by local AI model - your data stays on your computer, 100% private")

with st.sidebar:
    st.header("⚙️ Settings")
    model_choice = st.selectbox(
        "Choose AI Model",
        ["qwen2.5:7b", "qwen2.5:14b"],
        index=0,
        help="7B is faster, 14B is smarter"
    )
    st.markdown("---")
    st.subheader("📋 Quick Examples")
    if st.button("📊 Basic Statistics"):
        st.session_state.quick_request = "Calculate basic statistics for all numeric columns: count, mean, min, max. Show as a table."
    if st.button("🧹 Data Cleaning"):
        st.session_state.quick_request = "Clean the data: remove duplicate rows, fill missing numeric values with 0, fill missing text values with empty string. Return the cleaned dataframe."
    if st.button("📈 Top 10 Analysis"):
        st.session_state.quick_request = "Sort the data by the first numeric column in descending order. Show only the top 10 rows."
    if st.button("🔄 Pivot Table"):
        st.session_state.quick_request = "Create a pivot table. Use first text column as index, second text column as columns, and first numeric column as values. Use sum."

if 'quick_request' not in st.session_state:
    st.session_state.quick_request = ""
if 'result_df' not in st.session_state:
    st.session_state.result_df = None
if 'generated_code' not in st.session_state:
    st.session_state.generated_code = ""

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📁 Upload Data")
    uploaded_file = st.file_uploader("Choose a file", type=['xlsx', 'xls', 'csv'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"File loaded successfully! {len(df)} rows, {len(df.columns)} columns")
            with st.expander("Preview data"):
                st.dataframe(df.head())
                
            st.session_state.original_df = df
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")

with col2:
    st.subheader("💬 Your Request")
    user_request = st.text_area("Describe what you want to do with the data", 
                                 value=st.session_state.quick_request,
                                 height=120,
                                 placeholder="e.g., Calculate total sales by category and find the top 5 categories")
    
    process_button = st.button("🚀 Process with AI", type="primary", use_container_width=True)

if process_button:
    if uploaded_file is None:
        st.error("Please upload an Excel or CSV file first.")
    elif not user_request.strip():
        st.error("Please describe what you want to do.")
    else:
        with st.spinner("AI is analyzing your data and generating code..."):
            try:
                client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
                
                df_head = st.session_state.original_df.head(5).to_string()
                dtypes_info = st.session_state.original_df.dtypes.to_string()
                
                prompt = f"""
DataFrame 'df' info:
Columns and types:
{dtypes_info}

First 5 rows:
{df_head}

User wants: {user_request}

Write Python pandas code. Store result in variable 'result_df' as a DataFrame.
Only output code, no explanations, no markdown.
"""
                
                response = client.chat.completions.create(
                    model=model_choice,
                    messages=[
                        {"role": "system", "content": "You are a Python pandas expert. Output only clean executable code. No markdown, no explanations, no talk."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=1000
                )
                
                code = response.choices[0].message.content.strip()
                code = code.replace("```python", "").replace("```", "").strip()
                
                st.session_state.generated_code = code
                
                local_vars = {'df': st.session_state.original_df.copy(), 'pd': pd, 'io': io}
                exec(code, {}, local_vars)
                result_df = local_vars.get('result_df', None)
                
                if result_df is not None and isinstance(result_df, pd.DataFrame):
                    st.session_state.result_df = result_df
                    st.success("✅ Processing complete!")
                else:
                    st.warning("Result not found or not a DataFrame. Check code below.")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
                if st.session_state.generated_code:
                    with st.expander("View generated code"):
                        st.code(st.session_state.generated_code)

if st.session_state.result_df is not None:
    st.markdown("---")
    st.subheader("📊 Results")
    
    result_df = st.session_state.result_df
    st.dataframe(result_df, use_container_width=True)
    
    col3, col4, col5 = st.columns([1, 1, 1])
    
    with col3:
        csv = result_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="processed_result.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col4:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False, sheet_name='Results')
        excel_data = output.getvalue()
        st.download_button(
            label="📥 Download as Excel",
            data=excel_data,
            file_name="processed_result.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col5:
        with st.expander("🔍 View AI Code"):
            st.code(st.session_state.generated_code)

st.markdown("---")
st.caption("💡 Tip: Try the quick example buttons in the sidebar to see what this tool can do!")
