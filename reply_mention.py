import praw
import os

#gives link to a gallery, but not to the individual images

# Create the reddit instance
class reddit_bot:
    #reddit = praw.Reddit("reddit-bot")
    #mentions = reddit.inbox.mentions()
    def __init__(self):
        self.reddit = praw.Reddit("reddit-bot")
        self.mentions = self.reddit.inbox.mentions()

    def open_list(self):
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
        return posts_replied_to

    def checkout_mention(self, mention, posts_replied_to):
        parent_id = mention.parent()
        message = ""
        if parent_id not in posts_replied_to:
            '''
            this would make it so we can only call the bot once per post
            or should it be once per comment? (unlimited)
            '''

            message = "python is statically and dynamically typed ~"
            parent = self.reddit.submission(id=parent_id)
            images = []
            if '.jpg' or '.jpeg' or '.png' or ".jfif" in parent.url:
                # this works with the case where the image might have some specific formatand doesn't end in .jpg...
                image_URL = parent.url
                images.append(parent.url)
                if ('.jpg' or '.jpeg' or '.png' or ".jfif" in parent.selftext) and len(parent.selftext) != 0:
                    '''
                  Had to account for the case where for some reason the keys would be foud in the selftext, but the
                  selftext was actually empty. Also had to work around whether or not somebody adds text to the original post.
                  Also had to work around when someone puts a caption to the image, there is an extra ')' at the end.
                  This might break if somebody posts other links in a post with an image in it.
                    '''
                    images = [] #reset images
                    num_images = parent.selftext.count("https://")  # check how many links we have total in the text
                    selftext = parent.selftext
                    for i in range(num_images):
                        unstripped_URL = selftext.split("https://")[i+1]  # for each link, take the split section with the actual part of the link (caption removed)
                        image_URL = unstripped_URL.split(')')[0]  # strip the closing' ) ' and the rest of remaining selftext
                        if '.jpg' or '.jpeg' or '.png' or ".jfif" in image_URL:  # use this to confirm it's a link to an image, and not to another site
                            images.append(image_URL)  # add it to our list of links to print

                message += "\n\nImage found! \n\nImage URL(s): " + str(
                    images)  # a double \n, marks for a newline in reddit
            else:
                message += "\n\nNo Image found in post!"

            print("***Message:\n", message)
            print("\nEnd of Message***")
            print("=============================\n\n")
        return message, parent_id

    def reply(self,mention, message):
        mention.reply(message)
        '''
        there is a limit to how often you can do this
        comment the mention.reply line when testing, and only want to see prints
        '''
    def add_to_list(self, parent_id, posts_replied_to):

        # Store the current id into our list
        posts_replied_to.append(parent_id) #comment out when testing
        with open('posts_replied_to.txt', 'w') as f:
            for post_id in posts_replied_to:
                f.write(post_id + '\n')
    def run(self):
        posts_replied_to = self.open_list()
        for mention in self.mentions:
            msg, parent_id = self.checkout_mention(mention, posts_replied_to)
            # if(len(msg) > 0):
            # bot.reply(mention, msg)
            # bot.add_to_list(parent_id, posts_replied_to)
def main():
    bot = reddit_bot()
    bot.run()

if __name__ == "__main__":
    main()

