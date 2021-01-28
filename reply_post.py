import praw
import pdb
import re
import os
import time
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

# Get the top limited values from the given subreddit
subreddit = reddit.subreddit('pythonforengineers')
i=0
while True:
    for submission in subreddit.hot(limit=5):

        # If we haven't replied to this post before
        if submission.id not in posts_replied_to:

            # Do a case insensitive search
            if re.search('FTP', submission.title, re.IGNORECASE):
                # Reply to the post
                submission.reply('python is statically and dynamically typed ~')
                print('Bot replying to: ', submission.title)

                # Store the current id into our list
                posts_replied_to.append(submission.id)
        for comment in submission.comments:
            if comment.id not in posts_replied_to:

                # Do a case insensitive search
                if re.search('FTP', comment.body, re.IGNORECASE):
                    # Reply to the post
                    comment.reply('python is statically and dynamically typed ~')
                    print('Bot replying to: ', comment.body)

                    # Store the current id into our list
                    posts_replied_to.append(comment.id)
    # Write our updated list back to the file
    with open('posts_replied_to.txt', 'w') as f:
        for post_id in posts_replied_to:
            f.write(post_id + '\n')
    time.sleep(5)
    i+=1
    print("iteration ",i)
