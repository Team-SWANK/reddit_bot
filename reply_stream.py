import praw
import os
import re
# Create the reddit instance
reddit = praw.Reddit('reddit-bot')
while True:
    i = 0 #counting and printing how many comments the stream has visited
    mentions = reddit.inbox.mentions
    stream = praw.models.util.stream_generator(mentions, skip_existing= True)
    print(type(mentions))
    for comment in stream:
        print("iteration:",i)
        i += 1
        if re.search('u/PhotoSenseBot', comment.body, re.IGNORECASE):

            message = "python is statically and dynamically typed ~"
            print('Bot replying to: ', comment.body)

           # parent_url = comment.submission()
            parent_id = comment.parent()
            print("Comment URL:", comment.submission)
            print("Comment id:", comment.id)
            parent = reddit.submission(id=parent_id)
            print(type(parent))
            print("Parent URL: ", parent)
            print("Parent ID:", parent_id)
            print("Selftext:",parent.selftext)
            if '.jpg' or '.jpeg' or '.png' in parent.url: #see reply_mention for reasoning behind this case
            # this works with the case where the image might have some specific format and doesn't end in .jpg...etc
                message += "\n\nImage found!"  # a triple ###, marks for a newline in reddit
            else:
                message += "\n\nNo Image found in post!"

            print(message)
            #comment.reply(message) #comment out when testing

