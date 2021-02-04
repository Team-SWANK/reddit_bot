import praw
import os
import re
# Create the reddit instance
reddit = praw.Reddit('reddit-bot')
while True:
    i = 0 #counting and printing how many comments the stream has visited
    for comment in reddit.subreddit("all").stream.comments():
        print(i)
        i += 1
        if re.search('u/PhotoSenseBot', comment.body, re.IGNORECASE):

            message = "python is statically and dynamically typed ~"
            print('Bot replying to: ', comment.body)

           # parent_url = comment.submission()
            parent_id = comment.parent()
            parent = reddit.submission(id=parent_id)
            print("Parent URL: ", parent.url)
            print("Parent ID:", parent_id)

            if '.jpg' or '.jpeg' or '.png' in parent.url: #see reply_mention for reasoning behind this case
            # this works with the case where the image might have some specific format and doesn't end in .jpg...etc
                message += "\n\nImage found!"  # a triple ###, marks for a newline in reddit
            else:
                message += "\n\nNo Image found in post!"

            print(message)
            #comment.reply(message) #comment out when testing

