**Large Language Models for Email Summarization of Personal Interactions**

This project develops a summarization tool using LLMs such as ChatGPT to generate concise text summaries of offline email conversations taken from the Enron Company Dataset. 
The project uses Python and served as a stepping stone for the main "live" email summarizer project. 

This repository is linked to an app that was made using Streamlit.  
Here is the link to the app in order to test this offline summarizer without needing to download or run anything locally:  
https://fypenron-4twucauqxxvmahba7grhik.streamlit.app/

Running this application locally:  
In order to run this summarizer tool locally, download the Python files within this repository and then install the necessary modules that are listed in the requirements.txt file. These can be downloaded using commands such as pip install [module name] for each module. E.g. pip install streamlit.  
After all the files are downloaded, adjust the file path in the filter_df() function within the data_processing.py file in order to reflect the local directory where emails.csv is stored.  
Following installation, the Streamlit app can be launched using the command:  
"streamlit run appEnron.py"
