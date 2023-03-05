import os
import praw
import openai
import random

# Get environment variables
openai.api_key = os.getenv("chatgpt_api_key")
client_id = os.environ['client_id']
client_secret = os.environ['client_secret']
username = os.environ['username']
password = os.environ['password']

reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent='<myBot>', username=username, password=password)

#for comment in reddit.subreddit('all').stream.comments(skip_existing=True):
#    print(comment.body)

completion = openai.ChatCompletion.create(
  model="gpt-3.5-turbo-0301",
  messages=[
    {"role": "system", "content": "You must pretend to reply as a redditor."},
    {"role": "user", "content": "Tell the world about the ChatGPT API in the style of a pirate."}
  ],
  temperature=round(random.uniform(0, 2), 1),
  n=1, 
)

print(completion.choices[0].message.content)