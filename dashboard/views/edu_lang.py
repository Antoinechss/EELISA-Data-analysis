import streamlit as st
import pandas as pd
import base64

def show_education_language_page(df):
    st.title("Education & Language Requirements on the European Job Market")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Education Requirements")
        
        col1_1, col1_2 = st.columns(2)
        
        with col1_1: 
            st.subheader("ISCED Classification")
            
            # Path to your PDF file
            pdf_path = "/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/processing/education_classification/ISCED-F 2013 - Detailed field descriptions.pdf"
            
            try:
                # Read PDF file
                with open(pdf_path, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                
                # Create download button
                st.download_button(
                    label="📄 Read ISCED Official Documentation",
                    data=pdf_bytes,
                    file_name="ISCED-F_2013_Detailed_field_descriptions.pdf",
                    mime="application/pdf"
                )
                
                
            except FileNotFoundError:
                st.error("❌ PDF file not found at the specified path")
                st.info("Please ensure the file exists at the correct location")
            except Exception as e:
                st.error(f"❌ Error reading PDF: {str(e)}")
        
        with col1_2: 
            st.subheader("Degree Requirements")
            # Add your degree requirements analysis here
            st.info("Degree analysis coming soon...")
    
    with col2:
        st.subheader("Language Requirements")
        # Add your language requirements analysis here
        st.info("Language analysis coming soon...")

