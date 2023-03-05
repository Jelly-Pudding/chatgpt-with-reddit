import os
import praw
import openai
import random
import time

# Get environment variables
openai.api_key = os.getenv("chatgpt_api_key")
client_id = os.environ['client_id']
client_secret = os.environ['client_secret']
username = os.environ['username']
password = os.environ['password']

reddit = praw.Reddit(client_id=client_id, client_secret=client_secret,
                     user_agent='<myBot>', username=username, password=password)

def get_new_comment():
    try:
        for comment in reddit.subreddit('all').stream.comments(skip_existing=True):
            if 30 <= len(comment.body) <= 300:
                if comment.parent_id.startswith('t3_'):
                    # top-level comment, no parent comment
                    print(f"\nThis is a top-level comment: {comment.body}\n")
                    return [comment, None]
                else:
                    # comment is a reply to another comment
                    parent_comment = reddit.comment(
                        comment.parent_id.split('_')[1])
                    # Check if the parent comment itself is a top-level comment.
                    if parent_comment.parent_id.startswith('t3_'):
                        if 30 <= len(parent_comment.body) <= 100:
                            print(
                                "\nThe comment has a parent. Comment: {comment.body}. Parent: {parent_comment.body}\n")
                            return [comment, parent_comment]
    except Exception as e:
        print(f"Error: ", e)
        return [None, None]

def get_chatgpt_reply(comment_lst):
    # i.e. there is no parent comment
    try:
        if comment_lst[1] == None:
            prompt = f"You have to reply as a reddit user. Do not respond as ChatGPT. \
Do not make it obvious that you are not human. This is the reddit comment you must respond to: \"{comment_lst[0].body}\""
        else:
            prompt = f"You have to reply as a reddit user. Do not respond as ChatGPT. \
Do not make it obvious that you are not human. This is the top-level reddit comment: \"{comment_lst[1].body}\". This is the comment \
which responds to the parent comment and it is also the comment you must respond to: \"{comment_lst[0].body}\""
        print(prompt)
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0301",
            messages=[
                {"role": "user",
                    "content": prompt}
            ],
            temperature=round(random.uniform(0, 1.4), 1),
            n=1,
            max_tokens=4000
        )
        print("\nreply " + completion.choices[0].message.content + "\n")
        return completion.choices[0].message.content

    except Exception as e:
        print("Error generating ChatGPT reply:", e)
        return None

def is_good_reply(reply):
    return not any(keyword in reply for keyword in ["policies", "violates", "unable to provide", "as a reddit user"])

while True:
    comment_lst = get_new_comment()
    if comment_lst[0] is not None:
        chatgpt_reply = get_chatgpt_reply(comment_lst)
        if chatgpt_reply is not None and is_good_reply(chatgpt_reply.lower()):
            comment_lst[0].reply(chatgpt_reply)
        else:
            print("\nbad comment detected! :(\n")
    else:
        print("\nError getting new comment, sleeping for a bit...\n")
    print("sleeping...")
    time.sleep(1000)
    print("done sleeping...")
