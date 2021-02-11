import praw
import os

#gives link to a gallery, but not to the individual images

# Create the reddit instance
class reddit_bot:
    def __init__(self):
        self.reddit = praw.Reddit("reddit-bot")
        self.mentions = self.reddit.inbox.mentions
        self.stream = praw.models.util.stream_generator(self.mentions, skip_existing=True)

    def parse_flags(self, text):
        flag_messages = ""
        flag_list = [] #this will hold all flags that we want to use
        flag_descriptions = [] #this will hold all flag description or names by index for the bot to respond with
        test_list = ["ab","cd","ef","ps","a"]#list of flags for testing responses
        #if test_list in text: # don't want to use this because we need to know exactly which flag is being used
        for flag in test_list:
            if flag in text:
                loc = text.find(flag) #this implementation will only return the index of the first instance of our string
                            #if we really want to, we can count all instance, and check all instances
                if loc != 0 and text[loc-1] == '-':
                    print("\nFlag found: -",flag,"")
                    flag_messages += "\n\n\nFlag found: -" + flag
        return flag_messages

    def checkout_mention(self, mention):
        parent_id = mention.parent()
        message = ""
        '''
            this would make it so we can only call the bot once per post
            or should it be once per comment? (unlimited)
        '''

        message = "python is statically and dynamically typed ~"
        parent = self.reddit.submission(id=parent_id)
        images = []
        try:
            if '.jpg' or '.jpeg' or '.png' or ".jfif" in parent.url:
                # this works with the case where the image might have some specific formatand doesn't end in .jpg...
                image_URL = parent.url
                images.append(parent.url)
                message += "\n\nImage found! \n\nImage URL(s): " + str(images)  # a double \n, marks for a newline in reddit

            elif ('.jpg' or '.jpeg' or '.png' or ".jfif" in parent.selftext) and len(parent.selftext) != 0:
                    '''
                Had to account for the case where for some reason the keys would be foud in the selftext, but the
                  selftext was actually empty. Also had to work around whether or not somebody adds text to the original post.
                    Also had to work around when someone puts a caption to the image, there is an extra ')' at the end.
                    This might break if somebody posts other links in a post with an image in it.
                    '''
                    images = [] #reset images
                    num_images = parent.selftext.count("https://")  # check how many links we have total in the text
                    selftext = parent.selftext
                    print("selftext: ",selftext)
                    print("\n***")
                    for i in range(num_images):
                        unstripped_URL = selftext.split("https://")[i+1]  # for each link, take the split section with the actual part of the link (caption removed)
                        image_URL = unstripped_URL.split(')')[0]  # strip the closing' ) ' and the rest of remaining selftext
                        if '.jpg' or '.jpeg' or '.png' or ".jfif" in image_URL:  # use this to confirm it's a link to an image, and not to another site
                            images.append(image_URL)  # add it to our list of links to print
                    print(type(mention))
                    message += "\n\nImage found! \n\nImage URL(s): " + str(images)  # a double \n, marks for a newline in reddit
            else:
                message += "\n\nNo Image found in post!"
            message += self.parse_flags(str(mention.body))
            print("***Message:\n", message)
            print("\nEnd of Message***")
            print("=============================\n\n")
        except Exception as e:
            print(e.__traceback__)
            return "This bot does not reply to comments! Only to initial image posts! :)", parent_id
        return message, parent_id

    def reply(self,mention, message):
        mention.reply(message)
        '''
        there is a limit to how often you can do this
        comment the mention.reply line when testing, and only want to see prints
        '''

    def run(self):
        for mention in self.stream:
            msg, parent_id = self.checkout_mention(mention)
            if(len(msg) > 0):
                self.reply(mention, msg)
            # bot.add_to_list(parent_id, posts_replied_to)
def main():
    bot = reddit_bot()
    bot.run()

if __name__ == "__main__":
    main()

