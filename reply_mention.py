import praw
import os

#gives link to a gallery, but not to the individual images

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
    parent_id = mention.parent()
    if parent_id not in posts_replied_to:
        '''
        this would make it so we can only call the bot once per post
        or should it be once per comment? (unlimited)
        '''
        message = "python is statically and dynamically typed ~"
        parent = reddit.submission(id=parent_id)

        ###for debugging/testing purposes
        print("\nmention found")
        print('Bot replying to: ', mention.body)

        print("Parent URL: ", parent.url)
        print("Parent_id:", parent_id)
        print("Comment_id:", mention.id)
        ###
        #if (parent.url).endswith(('jpg', 'jpeg', 'png')): #this only works if the post ends with what's in the tuple
        if '.jpg' or '.jpeg' or '.png' or ".jfif" in parent.url:
        #this works with the case where the image might have some specific formatand doesn't end in .jpg...
            image_URL = parent.url
            images = [parent.url]
            if ('.jpg' or '.jpeg' or '.png' or ".jfif" in parent.selftext) and len(parent.selftext) != 0:
                '''
              Had to account for the case where for some reason the keys would be foud in the selftext, but the
              selftext was actually empty. Also had to work around whether or not somebody adds text to the original post.
              Also had to work around when someone puts a caption to the image, there is an extra ')' at the end.
              This might break if somebody posts other links in a post with an image in it.
                '''
                images = []
                num_images = parent.selftext.count("https://") #check how many links we have total in the text

                for i in range(num_images):
                    unstripped_URL = parent.selftext.split("https://")[1] #for each link, take the split section with the actual part of the link (caption removed)
                    image_URL = unstripped_URL.split(')')[0] #strip the closing' ) ' and the rest of remaining selftext
                    if '.jpg' or '.jpeg' or '.png' or ".jfif" in image_URL: #use this to confirm it's a link to an image, and not to another site
                        images.append(image_URL) #add it to our list of links to print

            message += "\n\nImage found! \n\nImage URL(s): " + str(images) # a double \n, marks for a newline in reddit
        else:
            message += "\n\nNo Image found in post!"
        ## More debugging prints
        print("***Selftext:",parent.selftext)
        print("\n***")

        print("Permalink:",parent.permalink)

        print("***Message:\n", message)
        print("\nEnd of Message***")

        print("=============================\n\n")
        ##
        # mention.reply(message)
        '''
        there is a limit to how often you can do this
        comment the mention.reply line when testing, and only want to see prints
        '''
        # Store the current id into our list
        #posts_replied_to.append(parent_id) #comment out when testing

# Write our updated list back to the file
with open('posts_replied_to.txt', 'w') as f:
    for post_id in posts_replied_to:
        f.write(post_id + '\n')
