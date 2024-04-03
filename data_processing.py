import pandas as pd
import email
import ast

def get_text_from_email(msg):
    '''To get the content from email objects'''
    parts = []
    for part in msg.walk():
        if part.get_content_type() == 'text/plain':
            parts.append(part.get_payload() )
    return ''.join(parts)

def split_email_addresses(line):
    '''To separate multiple email addresses'''
    if line:
        addrs = line.split(',')
        addrs = frozenset(map(lambda x: x.strip(), addrs))
    else:
        addrs = None
    return addrs

def filter_df():
    df = pd.read_csv("emails.csv")
    s_email_df = df.sample(100_000) # dont take the whole lot. Just sample 100000 emails. Thats more than enough
    messages = list(map(email.message_from_string, s_email_df['message']))
    s_email_df.drop('message', axis=1, inplace=True)
    # Get fields from parsed email objects
    keys = messages[0].keys()
    for key in keys:
        s_email_df[key] = [doc[key] for doc in messages]
    # Parse content from emails
    s_email_df['content'] = list(map(get_text_from_email, messages))
    # Split multiple email addresses
    s_email_df['From'] = s_email_df['From'].map(split_email_addresses)
    s_email_df['To'] = s_email_df['To'].map(split_email_addresses)

    # Extract the root of 'file' as 'user'
    s_email_df['user'] = s_email_df['file'].map(lambda x:x.split('/')[0])
    del messages
    s_email_df.reset_index(drop=True, inplace=True)
    s_email_df = s_email_df.drop_duplicates(subset='content', keep='first')

    # Convert each element in the 'From' column to a string
    s_email_df['From'] = s_email_df['From'].apply(lambda x: str(list(x)[0]))

    # Drop remaining NaN values in the 'To' column
    s_email_df = s_email_df.dropna(subset=['To'])


    s_email_df['To'] = s_email_df['To'].apply(lambda x: str(list(x)))
    s_email_df['To'] = s_email_df['To'].apply(ast.literal_eval)
    # Step 2: Create pairs of people for each conversation
    s_email_df['Pairs'] = s_email_df.apply(lambda row: [(row['From'], to) for to in row['To']], axis=1)

    # Step 3: Count the occurrences of each pair
    pair_counts = s_email_df['Pairs'].explode().value_counts()
    return s_email_df


def process_emails():
    df = filter_df()
    return df

