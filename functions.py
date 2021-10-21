import collections
import datetime
import glob
import itertools
import json
import os
import scipy.fftpack

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import pylab as pl
import scipy as sp

from collections import Counter
from itertools import compress
from scipy.interpolate import interp1d
from wordcloud import WordCloud,  STOPWORDS

##############################################################################
############# Classes   ######################################################
##############################################################################

class AccountData:
    def __init__(self, data, name):
        self.name       = name
        self.rawdata    = data
    
    def tweetsperday(d,average=False,window=3):
        tpd = d.rawdata
        tpd = tpd.groupby(pd.Grouper(key="cr_time", freq="1D")).sum()
        tpd = tpd[['counter']]
        if average:
            tpd = tpd.rolling(window).mean()
        return tpd

    def retweetsperday(d,average=False,window=3):
        rtpd = d.rawdata
        rtpd = rtpd.groupby(pd.Grouper(key="cr_time", freq="1D")).sum()
        rtpd = rtpd[['is_retweet']]
        if average:
            rtpd = rtpd.rolling(window).mean()
        return rtpd  
    
    def retweetratio(d,nooriginals=True,average=False,window=3):
        ot  = d.tweetsperday()
        t   = d.tweetsperday().values.flatten()
        rt  = d.retweetsperday().values.flatten()
        ratio = np.divide(rt,t)
        ot['rt_ratio'] = ratio
        if nooriginals:
            ot = ot.drop(['counter'], axis=1) 
        if average:
            ot = ot.rolling(window).mean()
        return ot
    
    def earliest(d):
        return min(d.rawdata['cr_time'])
    
    def latest(d):
        return max(d.rawdata['cr_time'])
    
    def fft(d, tweet = 'tweet'):
        if tweet == 'retweet':
            return sp.fftpack.fft([d.retweetsperday().T.values]).flatten()
        elif tweet == 'ratio':
            return sp.fftpack.fft([d.retweetratio().T.values]).flatten()
        else:
            return sp.fftpack.fft([d.tweetsperday().T.values]).flatten()
        
    def psd(d):
        fft     = d.fft()
        psd     = abs(fft) **2
        middle  = len(psd) // 2
        psd     = psd[:middle]
        return psd
    
    def recent_time_interval(d,numdays=365):
        base = datetime.datetime.today()
        return [base - datetime.timedelta(days=x) for x in range(numdays)]
    
    def find_hashtags(d,tuples=True, noduplicates=False):
        a = d.rawdata['hashtags'].values.flatten()
        b = []
        for n in a:
            b.append(n)
            b = [c for c in b if b!=[] and c]
        if tuples == False:
            b = [item for sublist in b for item in sublist]
        if noduplicates == True: # If True, then tuples must be False!
            b = list(set(b)) 
        return b
    
    def list_tweets(d, content="tweets"):
        b = d.rawdata
        test  = [x for x in b["text"]]
        test2 = [x for x in b["is_retweet"]]
        if content == "tweets":
            tweetlist = [i for (i,v) in zip(test,test2) if v==False]
        else:
            tweetlist = [i for (i,v) in zip(test,test2) if v==True]
        return tweetlist
        


##############################################################################
############# Functions ######################################################
##############################################################################

# DATA INPUT
# ===========================================================================
def prepare_data(names_list,dir_data_path):
    new_database = merge_data(names_list,dir_data_path)
    new_database = turn2datetime(new_database)
    new_database = data2dataframe(new_database,names_list)
    new_database = add_counter_ones(new_database)    
    return new_database

def merge_data(names_list,data_dir):          
    data_dict = {}
    for n in names_list:
        temporary_list = []
        found_files = []
        for name in glob.glob(data_dir+'/'+ n +'*'):
            found_files.append(name)
        for f in found_files:
            with open(f,'r') as openfile:
                temporary_list = temporary_list + json.load(openfile)
        data_dict[n] = temporary_list  
    return data_dict
       
def read_data(directory, namelist):
    # Read data and merge in a dict of list-of-dicts
    database = prepare_data(namelist,directory)
    collection = {}
    for n in namelist:
        collection[n] = AccountData(database[n],n)
    return collection

# TOOLS
# ===========================================================================

def add_counter_ones(old_database):
    database_2 = old_database.copy()
    for username in list(old_database.keys()):
        ones                    = [1] * len(old_database[username])
        database_2[username]['counter']   = ones
    return database_2

def color_list(G):
    c = list(G.nodes())
    i = 0
    for g in G.nodes():
        c[i] = G.nodes[g]['colour']
        i += 1
    return c

def data2dataframe(old_dict,names_list):
    new_dict = {}
    for n in names_list:
        new_dict[n] = pd.DataFrame(old_dict[n])
    return new_dict


def flatten(t):
    return [item for sublist in t for item in sublist]

def turn2datetime(data_dict):
    new_dict = data_dict.copy()
    for username in list(new_dict.keys()):
        for status in new_dict[username]:
            status['cr_time'] = datetime.datetime.strptime(status['cr_time'],"%d %m %Y-%H %M %S")
    return new_dict



# NETWORK ANALYSIS
# ===========================================================================

def hashtag_network(dbase, mode='weighted'):
    account_color = "red"
    hashtag_color  = "blue"
    G = nx.Graph()
    # Add accounts as nodes
    G.add_nodes_from(list(dbase.keys()), typ='account', colour=account_color)
    # add hashtags as nodes
    if mode == 'unweighted':
        for n in list(dbase.keys()):
            hashtags = dbase[n].find_hashtags(tuples=False, noduplicates=True)
            G.add_nodes_from(hashtags, typ = 'hashtag', colour=hashtag_color)
            for h in hashtags:
                G.add_edge(n,h)
    if mode == 'weighted':
        for n in list(dbase.keys()):
            hashtags = dbase[n].find_hashtags(tuples=False, noduplicates=False)
            for h in hashtags:
                if G.has_edge(n,h):
                    G.edges[n,h]['weight'] = G.edges[n,h]['weight'] + 1
                else:
                    G.add_node(h,typ='hashtag', colour=hashtag_color)
                    G.add_edge(n,h, weight = 1)  
    return G

def deg_histogram(G):
    # Note: Easier done with GEPHI or similar software.
    plt.clf()  
    degree_sequence = sorted([d for n, d in G.degree()], reverse=True)
    degreeCount = collections.Counter(degree_sequence)
    deg, cnt = zip(*degreeCount.items())
    
    fig, ax = plt.subplots()
    plt.bar(deg, cnt, width=0.80, color="b")
    plt.title("Degree Histogram")
    plt.ylabel("Count")
    plt.xlabel("Degree")
    ax.set_xticks([d + 0.4 for d in deg])
    ax.set_xticklabels(deg)
    
    plt.savefig("results\\test_deg.png")
    plt.clf()   

def reduce_network(G):
    H = G.copy()
    for g in G.nodes():
        if G.degree[g] < 2:
            H.remove_node(g)
    return H



# PLOTTING
# ===========================================================================

def plot_dailytweets(data,namelist):
    for n in namelist:
        # keep the interactive window from opening
        plt.ioff()
        
        testClass = data[n]
        
        # Determine values to plot
        data_line   = testClass.tweetsperday()
        x           = data_line.index
        y_mean      = [np.mean(testClass.tweetsperday().counter.values)]*len(testClass.tweetsperday())
        y           = data_line.values
        
        fig,ax      = plt.subplots()
        
        # the actual plotting
        ax.plot(x,y, label='Tweets per day')
        ax.plot(x, y_mean, label='Mean', linestyle='--')
        
        ax.legend(loc='upper right')
        ax.set(xlabel="Date", ylabel="Tweets per day")
        plt.title('Daily tweets ' + testClass.name)
        
        # set x-axis date format
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.'))
        fig.autofmt_xdate()
        
        #plt.show()
        plt.savefig("results\\DT_"+testClass.name+".png")
 
def plot_PSD(data, namelist):
    for n in namelist:
        plt.clf()
        # cutoff = 30
        # plt.plot(DataCollection[n].psd()[0:cutoff])
        plt.plot(data[n].psd())
        plt.ylabel('PSD')
        plt.xlabel('Frequency [1/days]')
        plt.suptitle('PSD of ' + n)
        plt.savefig("results\\PSD_"+n+".png")  

def plot_retweetratio(data,namelist):
    for n in namelist:
        plt.clf()
        # keep the interactive window from opening
        plt.ioff()
        testClass = data[n]
        
        # Determine values to plot
        data_line   = testClass.retweetratio()
        x           = data_line.index
        y           = data_line.values
        y           = [a[0] for a in y]
        
        # the actual plotting
        fig,ax      = plt.subplots()
        data_line   = ax.bar(x,y, label='Amount of retweets per day')
        #legend      = ax.legend(loc='upper right')
        ax.set(xlabel="Date", ylabel="Retweet ratio")
        plt.title('Retweet-to-tweet ratio ' + testClass.name)
        
        # set x-axis date format
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.'))
        fig.autofmt_xdate()
        
        #plt.show()
        plt.savefig("results\\RT_"+testClass.name+".png")   
        plt.clf()
    return

def plot_tweetlength(data,namelist):
    plt.ioff()
    for n in namelist:
        plt.clf()
        tweets      = data[n].rawdata.query("is_retweet == False")
        tweetlen    = [len(x) for x in tweets["text"]]
    
        y   = [tweetlen.count(x)*100/len(tweets) for x in range(0,281)]
        x   = [x for x in range(0,281)]
        
        plt.plot(x,y,"-", color="darkgreen")
        
        plt.suptitle(' Tweet length distribution\n of ' + n)
        plt.ylabel('P(L) [%]')
        plt.xlabel('Tweet length [characters]')
        plt.savefig("results\\TWEETLEN_"+n+".png")
        plt.clf()
        
            
def plot_wordclouds(data, namelist, 
                    h=1000, w=1080, 
                    maxwords=20, minword=4, minhash=2):
    irrel = "geht ab sind mehr dort nach des ihre bis aber will noch einer\
        soll da es sein zur mit e t co eine sich kann man dieses aus haben \
            wie keine hier werden wieder für einem als denn um bei gar \
                doch auch oder etwa ist nicht schon war zum welche wo hat \
                    nun wurde welche wo unsere damit den dem gibt ja mal \
                        vor dass einen alle https wird nur zu wie durch \
                            Und und von Von Der der Die die Das das wir \
                                ich du er sie auf im in unter über the a"
    irrel = irrel.split()
    STOPWORDS.update(irrel) 
    plt.ioff()
    
    for n in namelist:
        # keep the interactive window from opening
        plt.clf()
        tweets      = data[n].rawdata.query("is_retweet == False")
        
        hashs       = tweets["hashtags"].tolist()
        hashs       = flatten([x for x in hashs if x!=[]])
        hashs_huge  = " ".join(hashs)
        #hash_count  = Counter(hashs).most_common(5)
        
        texts_list  = tweets["text"].tolist()
        texts_huge  = " ".join(texts_list)
    
        
    
        fig, (ax1,ax2) = plt.subplots(1,2)
        
        wordcloud = WordCloud(background_color="white",
                              width=w, height=h,
                              max_words=maxwords,
                              min_word_length=minword).generate(texts_huge)
        hashcloud = WordCloud(background_color="white",
                              width=w, height=h,
                              max_words=maxwords,
                              min_word_length=minhash).generate(hashs_huge)
        
       
        ax1.imshow(wordcloud, interpolation="bilinear")
        ax2.imshow(hashcloud, interpolation="bilinear")
        ax1.title.set_text('MOST COMMON WORDS')
        ax2.title.set_text('MOST COMMON HASHTAGS')
        ax1.axis("off")
        ax2.axis("off")
        fig.suptitle("{}".format(n))
    
        plt.savefig("results\\CLOUDS_"+n+".png")





