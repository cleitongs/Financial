import streamlit as st
from modules.market_expectations_focus_survey import focus_market_expectations

def main():
    try:
        focus_market_expectations()
    except Exception as e:
        st.write(f"Error: {e}")

if __name__ == '__main__':
    main()