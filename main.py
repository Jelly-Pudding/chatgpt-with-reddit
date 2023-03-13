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
        for comment in reddit.subreddit('worldnews+politics+stupidpol+thesopranos').stream.comments(skip_existing=True):
            if comment.submission.is_self:
                continue # Skip text-based posts
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
                                "\nThe comment has a parent. Comment: {comment.body}. Parent: {parent_comment.body}\n")
                            return [comment, parent_comment, submission_title]
    except Exception as e:
        print(f"Error: ", e)
        return [None, None, None]

def get_chatgpt_reply(comment_lst):
    # i.e. there is no parent comment
    try:
        if comment_lst[1] == None:
            prompt = f"You have to reply as a sarcastic redditor. Do not respond as ChatGPT. \
Try to appear human. This is the title of the post: '{comment_lst[2]}'. You did not create this post. You are someone \
making a new comment and this is the reddit comment you must respond to (but remember the comment you are responding to responds to the post, not you): '{comment_lst[0].body}'"
        else:
            prompt = f"You have to reply as a reddit user. Be as sarcastic as possible. Do not respond as ChatGPT. \
Try to appear human. This is the title of the post: '{comment_lst[2]}'. This is the top-level reddit comment: '{comment_lst[1].body}'. You neither \
created the post nor the top-level comment. You must respond as a new commenter to this comment someone made which replied to the top-level comment (remember you are new to the conversation): \
'{comment_lst[0].body}'"

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
    return not any(keyword in reply for keyword in ["as a reddit user", "as an ai", "as a fellow redditor", "as a fellow reddit user"])

def remove_potential_quotation_marks(s):
    if s and s[0] in ['\'', '"'] and s[-1] in ['\'', '"'] and len(s) > 1:
        s = s[1:-1]
    return s

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
                cleaned_reply = remove_potential_quotation_marks(chatgpt_reply)
                comment_lst[0].reply(cleaned_reply)
            else:
                print("\nFailed moderation policies or the reply made was bad! :(\n")
        else:
            print("\nError getting new comment...\n")
        print("sleeping...")
        time.sleep(12600)
        print("done sleeping...")
    except Exception as e:
        print("Error replying: ", e)
        print("going... to sleep...")
        time.sleep(12600)