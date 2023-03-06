import os
import praw
import openai
import random
import time
import re
from keep_alive import keep_alive

# Get environment variables
openai.api_key = os.getenv("chatgpt_api_key")
client_id = os.environ['client_id']
client_secret = os.environ['client_secret']
username = os.environ['username']
password = os.environ['password']

reddit = praw.Reddit(client_id=client_id, client_secret=client_secret,
                     user_agent='<myBot>', username=username, password=password)

def found_url(comment):
    url_regex = r'\b(https?://|www\.)[^\s/$.?#].[^\s]*\b'
    if re.match(url_regex, comment):
        print("\nFound a url in the comment!\n")
        return True
    return False

def get_new_comment():
    # Returns the comment, the parent comment, and the title
    try:
        for comment in reddit.subreddit('all').stream.comments(skip_existing=True):
            if 30 <= len(comment.body) <= 300 and not found_url(comment.body):
                submission_title = comment.submission.title
                if comment.parent_id.startswith('t3_'):
                    # top-level comment, no parent comment
                    print(f"\nThis is a top-level comment: {comment.body}\n")
                    return [comment, None, submission_title]
                else:
                    # comment is a reply to another comment
                    parent_comment = reddit.comment(
                        comment.parent_id.split('_')[1])
                    # Check if the parent comment itself is a top-level comment.
                    if parent_comment.parent_id.startswith('t3_'):
                        if 30 <= len(parent_comment.body) <= 100 and not found_url(parent_comment.body):
                            print(
                                f"\nThe comment has a parent. Comment: {comment.body}. Parent: {parent_comment.body}\n")
                            return [comment, parent_comment, submission_title]
    except Exception as e:
        print(f"Error: ", e)
        return [None, None, None]

def get_chatgpt_reply(comment_lst):
    # i.e. there is no parent comment
    try:
        if comment_lst[1] == None:
            prompt = f"You have to reply as a reddit user. You can pretend to be happy, sad, sarcastic, or anything else really. Do not respond as ChatGPT. \
Do not make it obvious that you are not human. This is the title of the post: {comment_lst[2]}. This is the reddit comment you must respond to: {comment_lst[0].body}"
        else:
            prompt = f"You have to reply as a reddit user. You can pretend to be happy, sad, sarcastic, or anything else really. Do not respond as ChatGPT. \
Do not make it obvious that you are not human. This is the title of the post: {comment_lst[2]}. This is the top-level reddit comment: {comment_lst[1].body}. This is the comment \
responding to the top-level comment and it is also the comment you must respond to in turn: {comment_lst[0].body}"
        print(f"\n{prompt}\n")

        if fails_moderation(prompt):
            print("\nThe prompt triggers one of ChatGPT's many stupid policies\n")
            return None
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0301",
            messages=[
                {"role": "user",
                    "content": prompt}
            ],
            temperature=1,
            n=1
        )
        print("\nreply " + completion.choices[0].message.content + "\n")
        return completion.choices[0].message.content

    except Exception as e:
        print("Error generating ChatGPT reply:", e)
        return None

def is_good_reply(reply):
    return not any(keyword in reply for keyword in ["as a reddit user", "as an ai", "as a fellow redditor", "as a fellow Reddit user"])

def fails_moderation(input_message):
    moderation_resp = openai.Moderation.create(input=input_message)
    return moderation_resp['results'][0]['flagged']

keep_alive()

while True:
    try:
        comment_lst = get_new_comment()
        if comment_lst[0] is not None:
            chatgpt_reply = get_chatgpt_reply(comment_lst)
            if chatgpt_reply is not None and is_good_reply(chatgpt_reply.lower()):
                comment_lst[0].reply(chatgpt_reply)
            else:
                print("\nFailed moderation policies or the reply made was bad! :(\n")
        else:
            print("\nError getting new comment...\n")
        print("sleeping...")
        time.sleep(1000)
        print("done sleeping...")
    except Exception as e:
        print("Error replying: ", e)
        print("going... to sleep...")
        time.sleep(1000)