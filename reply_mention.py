import praw
import os
# Create the reddit instance
reddit = praw.Reddit('reddit-bot')

# Have we run this code before? If not, create an empty list
if not os.path.isfile('posts_replied_to.txt'):
    posts_replied_to = []

# If we have run this code before, load the list of posts we have replied to
else:
    # Read the file into a list and remove any empty values
    with open('posts_replied_to.txt', 'r') as f:
        posts_replied_to = f.read()
        posts_replied_to = posts_replied_to.split('\n')
        posts_replied_to = list(filter(None, posts_replied_to))

#retrieve list of account mentions
mentions = reddit.inbox.mentions()
for mention in mentions:
    if mention.id not in posts_replied_to:
        print("mention found")
        mention.reply('python is statically and dynamically typed ~')
        print('Bot replying to: ', mention.body)

        # Store the current id into our list
        posts_replied_to.append(mention.id)

# Write our updated list back to the file

with open('posts_replied_to.txt', 'w') as f:
    for post_id in posts_replied_to:
        f.write(post_id + '\n')
