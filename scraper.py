import datetime
import json
import os
import tweepy



##############################################################################
############# auth section ###################################################
##############################################################################

# Enter your Twitter API credentials here. I'm not going to tell you mine ;)
consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""

# Creating the authentication object
# Setting your access token and secret
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# Creating the API object while passing in auth information
api = tweepy.API(auth) 


##############################################################################
############# Settings #######################################################
##############################################################################
# Change working directory to be safe
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# Is this your first running this script? If so, then  set this to True.
# As we have to obtain "memory" of what we scraped so far in the past,
# we save the most recent Tweet's IDs.
initial_run = False
tweetCount = 500
file_name_mid   = "maximum_id.txt"

# list of Twitter Accounts to follow. For example, I followed my hometown's
# official stuff, police, fire dept, local press and TV, 
# all factions in city council exept for CDU (not active), Die Linke 
# (no regional account), or Die Hannoveraner (no account)
names_list = ["hannover","regionhannover_","Polizei_H","Feuerwehr_H","HAZ",
              "neuepresse","SPDRatHannover", "gruenehannover", 
              "PiratenHannover","AfdHannover","PARTEI_Hannover",
              "BILD_Hannover","h1fernsehen"]


##############################################################################
############# functions def ##################################################
##############################################################################

def status2dict(status):
    '''
    Output tweet information from one 'status' object (a 'tweet')

    Parameters
    ----------
    status : models.Status
        A tweet saved as a 'status' object from tweepy.

    Returns
    -------
    idnr : int
        DESCRIPTION.
    cr_time : TYPE
        DESCRIPTION.
    text : str
        Text from the tweet. Is either .full_text from the extendend-tweet 
        itself or the .full_text from .retweeted_status.full_text.
    retweets : int
        Amount of retweets.
    favorites : int
        Amount of favorizations.
    hashtags : list of str
        List of strings, containing the hashtags used in the tweet.
    is_retweet : bool
        Describes whether the status is a retweet (true) or not (false)
    retw_id : integer
        ID of the original tweet if the status is a retweet. pd.nan otherwise
    orig_author : str
        Name of the original author if status is a retweet. pd.nan otherwise.

    '''
    # convenient function to get all information I want from a status object
    dictio                    = {}
    dictio["idnr"]            = status.id
    dictio["cr_time"]         = status.created_at.strftime("%d %m %Y-%H %M %S")
    dictio["retweets"]        = status.retweet_count
    dictio["favorites"]       = status.favorite_count
    dictio["is_retweet"]      = hasattr(status,"retweeted_status")
    if dictio["is_retweet"]:
        dictio["retw_id"]     = status.retweeted_status.id
        dictio["text"]        = status.retweeted_status.full_text.replace('\n', 
                                                                          ' ')
        dictio["orig_author"] = status.retweeted_status.author.screen_name
    else:
        dictio["retw_id"]     = None
        dictio["text"]        = status.full_text.replace('\n', ' ')
        dictio["orig_author"] = None

    dictio["hashtags"]      = [h['text'] for h in status.entities['hashtags']]
    return  dictio
    



def results2list_of_dict(search,name):
    '''
    Write the results of a search as a .json file and returns a test dict

    Parameters
    ----------
    search : list of models.ResultSet
        List of several results of api.user_timeline().
    name : list of strings
        List of names of the searches. Preferable the account names you read.
        
    Returns
    -------
    output_dict : TYPE
        A dictionary, with [list of dictionaries] as entries, each entry has
        a key according to the twitter user name.
        Example:
        output_dict['username'] results in [status, status, status,...] list,
        where each status is a dictionary according to 
        the output of status2dict()

    '''
    now = datetime.datetime.now().strftime("%d %m %Y-%H %M %S")
    output_dict = {}
    for n in range(len(search)):
        if len(search[n]) > 0:
            output_dict[name[n]] = [status2dict(stat) for stat in search[n]]
            file_name = "json\\" + name[n] + "_" + now + ".json"
            with open(file_name,'w') as outfile:
                json.dump(output_dict[name[n]],outfile)
    return output_dict
                
                
    
    
def initial_catch(API,namelist,init_count=20):
    '''
    Catch an initial set of tweets.

    Parameters
    ----------
    API : tweepy API handler object
        API handler to connect to Twitter.
    namelist : list of strings
        List of names of the searches. Preferable the account names you read.
    init_count : int
        Amount of tweets to go back in time. Standard is 20.

    Returns
    -------
    results : list of models.ResultSet
        List of several results of api.user_timeline().
    max_ids : list of integers
        ID of the tweets ('statuses') that are most recent. For later use.

    '''

    results = []
    for n in range(len(namelist)):
        name    = namelist[n]
        result = API.user_timeline(id=name, 
                                   count=init_count,
                                   tweet_mode="extended")
        results.append(result)       
    # create a max_id list
    max_ids = []
    for n in range(len(namelist)):
        max_ids.append(results[n][0].id) 
    return results,max_ids
    

        

def update_catch(API,namelist,maximum_ids):
    '''
    Update dataset and the maximum_ids list.

    Parameters
    ----------
    API : tweepy API handler object
        API handler to connect to Twitter.
    namelist : list of strings
        List of names of the searches. Preferable the account names you read.
    max_ids : list of integers
        ID of the tweets ('statuses') that are most recent in this catch.
        An updated version will be returned.

    Returns
    -------
    results : list of models.ResultSet
        List of several results of api.user_timeline(). Contain statuses since
        max_id
    new_max_id : list of integers
        ID of the tweets ('statuses') that are most recent. Updated now.

    '''
    
    new_max_id = maximum_ids.copy()
    results = []
    for n in range(len(names_list)):
        name    = namelist[n]
        result_new  = API.user_timeline(id=name, 
                                        since_id=maximum_ids[n],
                                        tweet_mode="extended")
        results.append(result_new)   
        if len(results[n]) > 0:
            new_max_id[n] = results[n][0].id    
    return results,new_max_id



##############################################################################
############# Data Collect ###################################################
##############################################################################

if initial_run:
    # For the initial run, create the initial catch.
    # Save the catch in .csv files.
    # Then, save the maximum ID in an external file.
    # THE MAXIMUM ID IS NECESSARY TO AVOID DUPLICATE IN THE DATA
    # [res,mid] = initial_catch(api, new_names,tweetCount)
    # res_dict  = results2list_of_dict(res,new_names)
    [res,mid] = initial_catch(api, names_list,tweetCount)
    res_dict  = results2list_of_dict(res,names_list)
    with open(file_name_mid,"w") as f:
        for m in mid:
            f.write(str(m) + "\n")
            
            
else:
    # Read the maximum IDs for use.
    mid = []
    with open(file_name_mid,"r") as f:
        for line in f:
            mid.append(int(line.strip()))    
            
    # Now update the results and the new maximum IDs       
    [new_res,new_mid] = update_catch(api,names_list,mid)
    res_dict  = results2list_of_dict(new_res,names_list)
    
    # Write the new maximum IDs to the file.
    with open(file_name_mid,"w") as f:
        for m in new_mid:
            f.write(str(m) + "\n")

# Write a log entry to check when the scrip was run last. Might come in handy.
datenow = datetime.datetime.now().strftime("%d %m %Y-%H %M %S")
with open('log.txt',"w") as f:
    f.write('This script has run without error at: ' + "\n" + datenow)


