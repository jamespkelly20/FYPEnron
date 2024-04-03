# E.G. Summarize all the emails between Jack and Jane from January 1st to February 1st into a 500 word output
import math
import sys
import re
import pandas as pd
import email
import openai
from bs4 import BeautifulSoup

#pip install beautifulsoup4
#pip install openai
#pip install openai==0.28

# Function to count words in a text
def count_words(text):
    return len(text.split())

# def clean_email_content(content):
#     # Remove forwarded and quoted text
#     cleaned_content = re.sub(r'(?s)---+ Forwarded.*?---+', '', content)
#     cleaned_content = re.sub(r'(?s)>.*?(\n|$)', '', cleaned_content)
#     # Remove lines starting with "Sent by:", email addresses, and dates
#     cleaned_content = re.sub(r'^Sent by:.*?(\n|$)', '', cleaned_content, flags=re.MULTILINE)
#     cleaned_content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', cleaned_content)
#     cleaned_content = re.sub(r'\b\d{1,2}/\d{1,2}/\d{4}\b', '', cleaned_content)

#     # Parse HTML content
#     soup = BeautifulSoup(cleaned_content, 'html.parser')
#     # Extract only text content
#     cleaned_content = soup.get_text(separator='\n')
#     #cleaned_content = re.sub(r'\s+', ' ', cleaned_content)

#     return cleaned_content.strip()
def clean_email_content(content):
    cleaned_content = re.sub(r'(?s)---+ Forwarded.*?---+', '', content)
    cleaned_content = re.sub(r'(?s)>.*?(\n|$)', '', cleaned_content)
    # Remove lines starting with "Sent by:", email addresses, and dates
    cleaned_content = re.sub(r'^Sent by:.*?(\n|$)', '', cleaned_content, flags=re.MULTILINE)
    cleaned_content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', cleaned_content)
    cleaned_content = re.sub(r'\b\d{1,2}/\d{1,2}/\d{4}\b', '', cleaned_content)

    # Parse HTML content
    soup = BeautifulSoup(cleaned_content, 'html.parser')
    # Extract only text content
    cleaned_content = soup.get_text(separator='\n')

    # Remove HTML Tags. I just want the actual email content.  Nothing else.
    cleaned_content = re.sub(r'<.*?>', '', cleaned_content)

    # Remove these div tag lines etc
    cleaned_content = re.sub(r'^(On|<div).*?(\n|$)', '', cleaned_content, flags=re.MULTILINE)

    return cleaned_content.strip()

#     # Parse HTML content
#     soup = BeautifulSoup(content, 'html.parser')
#     # Extract only text content
#     content = soup.get_text(separator='\n')
#     #cleaned_content = re.sub(r'\s+', ' ', cleaned_content)

#     return content.strip()

#words_per_chunk = math.floor(4096 / 2.2)

def calculate_words_per_chunk():
    return math.floor(4096 / 2.2)

def extract_chunks(text, words_per_summary):
    words_per_chunk = calculate_words_per_chunk()
    chunk_size=words_per_chunk-math.ceil(words_per_summary)
    words = text.split()
    total_words = len(words)
    for i in range(0, total_words, chunk_size):
        chunk = ' '.join(words[i:i+chunk_size])
        yield chunk

# Function to get emails and summarize
def get_emails_and_summarize(df, sender, recipient, start_date, end_date, total_words_in_output):
    words_per_chunk = calculate_words_per_chunk()
    # Step 1: Filter emails based on sender, recipient, and date range
    df['Date'] = pd.to_datetime(df['Date'], utc=True, errors='coerce') 
    start_date = pd.to_datetime(start_date, utc=True)
    end_date = pd.to_datetime(end_date, utc=True)
    filtered_emails = df[
    (
        ((df['From'] == sender) & (df['To'].apply(lambda x: recipient in x if isinstance(x, list) else False))) |
        ((df['To'] == sender) & (df['From'].apply(lambda x: recipient in x if isinstance(x, list) else False))) |
        ((df['From'] == recipient) & (df['To'].apply(lambda x: sender in x if isinstance(x, list) else False))) |
        ((df['To'] == recipient) & (df['From'].apply(lambda x: sender in x if isinstance(x, list) else False)))
    ) &
    ((df['Date'] >= start_date) & (df['Date'] <= end_date)) 
    ]

    # Check if there are any emails
    if filtered_emails.empty:
        print("No emails found between the specified sender and recipient.")
        error_message = "ERROR - NO EMAILS FOUND BETWEEN THE SPECIFIED ADDRESSES"
        return error_message
        sys.exit()  # Exit the function
        
    # Step 2: Sort emails by date
    filtered_emails = filtered_emails.sort_values(by='Date')
    filtered_emails['WordCount'] = filtered_emails['content'].apply(count_words)
    total_words_in_the_emails = filtered_emails['WordCount'].sum()
    print("TOTAL WORDS IN THE EMAILS: ", total_words_in_the_emails)
    
    concatenated_content = '\n'.join(filtered_emails['content'].astype(str).tolist())
    #print("TOTAL WORDS IN THE EMAILS together concatenated should be same: ", count_words(concatenated_content))
    cleaned_content = clean_email_content(concatenated_content)
    total_cleaned_content_count_words = count_words(cleaned_content)
    print("TOTAL WORDS cleaned content: ", total_cleaned_content_count_words)
    
    # Initialize variables
    chunks = []
    number_outputs=[]
    size_chunk=[]
    current_chunk = ""
    current_chunk_words = 0
    # Split the email content into chunks
    #words_per_chunk = math.floor(4096 / 2)  # model's maximum context length (INCLUDING THE GENERATED SUMMARY)
    # Iterate through each email
    #counter=0
    original_emails_info = []

    for i, email_content in enumerate(filtered_emails['content'].astype(str).tolist()):
        # Clean the email content
        cleaned_content = clean_email_content(email_content)
        cleaned_content_count_words = count_words(cleaned_content)
        print("FROM:", filtered_emails.iloc[i]['From'])
        print("To:", filtered_emails.iloc[i]['To'])
        print("DATE: ", filtered_emails.iloc[i]['Date'])
        original_email_info = {
            "From": filtered_emails.iloc[i]['From'],
            "To": filtered_emails.iloc[i]['To'],
            "Date": filtered_emails.iloc[i]['Date'],
            "Email": cleaned_content
        }
        original_emails_info.append(original_email_info)
        
        if (cleaned_content_count_words > words_per_chunk):#&& counter == 0:
            print("NOTE HERE IS A LARGE SIZED EMAIL/!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
            print("current_chunk_words before appending (previous EMAIL)", current_chunk_words, "\n")
            print("cleaned_content_count_words LARGE EMAIL CURRENT= ", cleaned_content_count_words, "\n") 
            if i != 0:
                chunks.append(current_chunk)
                size_chunk.append(current_chunk_words)           
                current_chunk_words = 0#1800
                current_chunk=""
            ##NOW WE BREAK UP THIS LARGE EMAIL HERE:
            #number_of_chunks_IN_LARGE_EMAIL = cleaned_content_count_words/words_per_chunk
            #for j in range Math.ceil(number_of_chunks_IN_LARGE_EMAIL):
            for word in cleaned_content.split():
                if current_chunk_words + 1 > words_per_chunk:
                    chunks.append(current_chunk)
                    size_chunk.append(current_chunk_words)
                    current_chunk = word
                    current_chunk_words = 1
                else:
                    current_chunk += " " + word
                    current_chunk_words += 1
            chunks.append(current_chunk)
            size_chunk.append(current_chunk_words)
            current_chunk = ""
            current_chunk_words = 0
                   
        else:
            #######
            # Access the next email content to calculate the current_output_words_in_chunk
            if i + 1 < len(filtered_emails['content'].astype(str).tolist()):
                next_email_content = filtered_emails['content'].astype(str).tolist()[i + 1]
                cleaned_next_content = clean_email_content(next_email_content)
                cleaned_next_content_count_words = count_words(cleaned_next_content)
                if (current_chunk_words + cleaned_content_count_words + cleaned_next_content_count_words) > (words_per_chunk):
                    current_output_words_in_chunk = ((current_chunk_words + cleaned_content_count_words)/total_words_in_the_emails)*total_words_in_output
                else:
                    current_output_words_in_chunk=0
            #######
            if (current_chunk_words + cleaned_content_count_words) > (words_per_chunk):#-current_output_words_in_chunk
                print("Content current num words = ", cleaned_content_count_words) #1800
                chunks.append(current_chunk)
                size_chunk.append(current_chunk_words)           
                current_chunk_words = cleaned_content_count_words#1800
                current_chunk=cleaned_content###WHAT IF THE LARGE EMAIL IS AFTER THIS ONE? WHAT WILL HAPEN...????
                #counter=0       
            else:
                current_chunk+= " " + cleaned_content
                print(cleaned_content)
                #print("\nCurrent CHUNK:\n ", current_chunk)
                print("\n\n")
                current_chunk_words+=cleaned_content_count_words
                print(cleaned_content_count_words)
                print("\n\n")
                print("currCHUNK WORDS", current_chunk_words)
                print("\n\n")
                #counter+=1

    #first we need to append the last chunks 
    chunks.append(current_chunk)
    size_chunk.append(current_chunk_words)
    #print(number_outputs)
    total_sum = sum(size_chunk)
    print("NEW TOTAL_SUM = ", total_sum)
    for element in size_chunk:
        percentage_of_chunk_words = element / total_sum
        current_output_words_per_chunk = math.floor(total_words_in_output * percentage_of_chunk_words)
        number_outputs.append(current_output_words_per_chunk)
    print(size_chunk)
    print(number_outputs)
    print(len(size_chunk))
    print(len(number_outputs))

    
    
    # Now, proceed with summarization for each chunk as before
    concatenated_summary = ""
    chunk_counter=0
    output_words_used = 0
    # Iterate through each chunk
    for i, chunk in enumerate(chunks):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Summarize the below email conversation in about {number_outputs[i]} words. Include important details and context:\n{chunk}.\nUse full sentances!"},
            ],
            #max_tokens=math.floor(number_outputs[i] * 1.5),
        )

        #chunk_summary = response['choices'][0]['text']
        chunk_summary = response['choices'][0]['message']['content']
        print(f"Mini Summarized Chunk:\n{chunk_summary}\nWord Count: {len(chunk_summary.split())}\n")
        concatenated_summary += f"\n{chunk_summary}"  # Add the mini summary to the concatenated summary
        print("\n")
    
    print("Final summarized version: \n", concatenated_summary)
    print(count_words(concatenated_summary))
    
    # Perform summarization for the entire concatenated summary
    input_NUMBER = count_words(concatenated_summary)
    #THIS IS only if the summarized chunks put together add up to more words than 1.5 times the specified output. THis means 
    # too long of a summary has been generated and we need to now summarize the summary. 
    if (input_NUMBER > 1.5*total_words_in_output):
        # Perform summarization for the entire concatenated summary
        remaining_words = total_words_in_output
        total_WORDS = input_NUMBER + remaining_words
        number_of_summaries = total_WORDS/words_per_chunk
        last_summary = number_of_summaries - int(number_of_summaries)
        number_of_words_in_last_summary = (last_summary/number_of_summaries) * remaining_words
        words_per_summary = remaining_words/number_of_summaries 

        final_final_summary = ""
        for i, chunk in enumerate(extract_chunks(concatenated_summary, words_per_summary)):
            summary_words = words_per_summary if i < (math.ceil(number_of_summaries) - 1) else number_of_words_in_last_summary
            #print(chunk)
            print("i=", i)
            print("CHUNK WORDS NUM: ", count_words(chunk))
            print("number_of_words_in_last_summary ", number_of_words_in_last_summary)
            print("SUMMARY WORDS: ", summary_words)
            print("number of summaries CEILING= ", math.ceil(number_of_summaries))
            #for i in Math.ceil(number_of_summaries):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Take out the most important points and summarize this summary into {math.floor(summary_words)} words. Include important details and context:\n{chunk}.\nUse full sentences! NB! The summary must not be more than {math.floor(summary_words) + math.floor(summary_words) * 0.1} words!"},
                ],
                #max_tokens=math.floor(summary_words * 1.4),
            )
            final_portion = response['choices'][0]['message']['content']
            print(f"Summarized Chunk:\n{final_portion}\nWord Count: {len(final_portion.split())}\n")
            final_final_summary+= final_portion

        print("Process completed.")
        print(final_final_summary)
        print(count_words(final_final_summary))
        return final_final_summary, original_emails_info
    else:
        return concatenated_summary, original_emails_info