# import streamlit as st
# import pandas as pd
# import openai  
# from summarization_function import get_emails_and_summarize
# from data_processing import process_emails
# import math
# import sys
# import re

# #sender_email = richard.shapiro@enron.com jeff.dasovich@enron.com

# # Streamlit UI
# st.set_page_config(page_title="Email Summarization", page_icon=":tada:", layout="wide")

# if "df" not in st.session_state:
#     st.session_state.df = None

# if "offline_summaries" not in st.session_state:
#     st.session_state.offline_summaries = {}

# with st.container():
#     st.title("Large Language Model (LLM) Email Summarizer (Enron)")

# with st.container():
#     st.write("---")
#     left_column, right_column = st.columns(2)
#     original_emails_info=[]
#     with left_column:

#         st.header("Summarize offine Enron company data")

#         # Input fields
#         #sender_email = 'richard.shapiro@enron.com' 'jeff.dasovich@enron.com'
#         email1 = st.text_input("Enter Email 1:")
#         email2 = st.text_input("Enter Email 2:")
#         start_date = st.date_input("Select Start Date:", min_value=pd.to_datetime('2000-01-01'))
#         end_date = st.date_input("Select End Date:", min_value=pd.to_datetime('2000-01-01'))
#         total_words_in_output = st.number_input("Enter Total Words in Output:", min_value=20, value=250, step=25)

#         #s_email_df = process_emails()
#         # Button to trigger summarization
#         if st.button("Summarize Emails"):
#             with st.spinner("Summarizing emails..."):
#                 s_email_df = process_emails()
#                 # Display a spinner while processing
#                 #summary, original_emails_info = get_emails_and_summarize(s_email_df, email1, email2, start_date, end_date, total_words_in_output)
#                 result = get_emails_and_summarize(s_email_df, email1, email2, start_date, end_date, total_words_in_output)
#                 print("LOOK HERE JAMESSSS")
#                 print(result)
#                 summary = result
#                 # st.session_state.offline_summaries["offline_emails"] = {
#                 #     "summary": summary,
#                 #     "original_emails_info": original_emails_info
#                 # }
#                 #summary = get_emails_and_summarize(s_email_df, email1, email2, start_date, end_date, total_words_in_output)
#                 st.session_state.offline_summaries["offline_emails"] = summary

#                 ## THis helps with rendering content correctly. With st.write some special characters were not rendered correcly.
#                 st.markdown("### Summary:")
#                 st.markdown(summary, unsafe_allow_html=True)
#                 # st.write("Summarized Output:")
#                 # st.write(summary)
                
#                 st.text("Summarization completed!")
#         if st.button("Clear Enron Emails Output"):
#             if "offline_emails" in st.session_state.offline_summaries:
#                 del st.session_state.offline_summaries["offline_emails"]

#     with right_column:
#         st.header("Here are the emails that were summarized: ")
#         for info in original_emails_info:
#             st.markdown(f"**From:** {info['From']}  \n**To:** {info['To']}  \n**Date:** {info['Date']}  \n**Email:** \n\n {info['Email']}  \n")


import streamlit as st
import pandas as pd
import openai  
from summarization_function import get_emails_and_summarize
import imaplib
from data_processing import process_emails
import math
import sys
import re
#sender_email = richard.shapiro@enron.com jeff.dasovich@enron.com
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Streamlit UI
st.set_page_config(page_title="Email Summarization", page_icon=":tada:", layout="wide")

if "df" not in st.session_state:
    st.session_state.df = None

if "offline_summaries" not in st.session_state:
    st.session_state.offline_summaries = {}

with st.container():
    st.title("Large Language Model (LLM) Email Summarizer")

with st.container():
    st.write("---")
    left_column, right_column = st.columns(2)
    original_emails_info=[]

    with left_column:
        st.header("Summarize Offline Enron Data")
        st.text("Example emails to test:\n richard.shapiro@enron.com and jeff.dasovich@enron.com \n jeff.dasovich@enron.com and ray.alvarez@enron.com \n christi.nicolay@enron.com and joseph.wagner@enron.com \n mary.cook@enron.com and david.portz@enron.com\n janet.butler@enron.com and mary.darveaux@enron.com\n\nNote that the date range must be between January 2000 and \nDecember 2001")

        emailSender = st.text_input("Enter first Email:")
        emailReceiver = st.text_input("Enter second Email:")
        startDate = st.date_input("Enter Start Date:", min_value=pd.to_datetime('2000-01-01'))
        endDate = st.date_input("Enter End Date:", min_value=pd.to_datetime('2000-01-01'))
        totalWordsInOutput = st.number_input("Enter Number Words in Output:", min_value=20, value=250, step=25)

        #s_email_df = process_emails()
        # Button to trigger summarization
        if st.button("Summarize Emails"):
            #s_email_df = get emails from IMAP SERVER INTO A DATAFRAME
            with st.spinner("Summarizing emails..."):
                # Display a spinner while processing
                try:
                    s_email_df = process_emails()
                    summary, original_emails_info = get_emails_and_summarize(s_email_df, emailSender, emailReceiver, startDate, endDate, totalWordsInOutput)
                    st.session_state.offline_summaries["off_emails"] = {
                        "summary": summary,
                        "original_emails_info": original_emails_info
                    }
                    #summary = get_emails_and_summarize(st.session_state.df, emailSender, emailReceiver, startDate, endDate, totalWordsInOutput)
                    st.session_state.offline_summaries["off_emails"] = summary
                    ## THis helps with rendering content correctly. With st.write some special characters were not rendered correcly.
                    st.markdown("### Summarized Output:")
                    st.markdown(summary, unsafe_allow_html=True)
                    st.text("Summarization completed!")
                except ValueError:
                    st.warning("Error occurred during summarization. \n\nEither one or more email addresses have not been found, or there is no existing emails within the specified date range!")
                except openai.error.InvalidRequestError as e:
                    st.warning(f"The total words in the emails exceeded the models capacity. \nPlease reduce the input and try again")
                except openai.error.RateLimitError:
                    # This block catches the RateLimitError specifically
                    st.warning("OPENAI has reached its limit. Try again soon or shorten the amount of emails you want summarized.")
                except Exception as e:
                    # Generic exception handler for any other exceptions
                    st.warning(f"An unexpected error occurred: {e}")
        if st.button("Clear Emails Output"):
            if "off_emails" in st.session_state.offline_summaries:
                del st.session_state.offline_summaries["off_emails"]


    with right_column:
        #st.header("The original emails")
        # Display original emails information
        st.header("Original Emails:")
        for info in original_emails_info:
            st.markdown(f"**From:** {info['From']}  \n**To:** {info['To']}  \n**Date:** {info['Date']}  \n**Email:** \n\n {info['Email']}  \n")

