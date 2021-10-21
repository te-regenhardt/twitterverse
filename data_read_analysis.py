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
############# Preamble  ######################################################
##############################################################################

from functions import *

dir_wrk = os.path.dirname(os.path.realpath(__file__))
dir_data= os.path.dirname(os.path.realpath(__file__)) + "\json"
os.chdir(dir_wrk)


names = ["hannover","regionhannover_","Polizei_H","Feuerwehr_H","HAZ",
              "neuepresse","SPDRatHannover", "gruenehannover", 
              "PiratenHannover","AfdHannover","PARTEI_Hannover","BILD_Hannover",
              "h1fernsehen"]





##############################################################################
############# Main Part ######################################################
##############################################################################

# DATA READ
# ===========================================================================
DataCollection = read_data(dir_data,names)
del dir_data, dir_wrk,



# NETWORK ANALYSIS
# ===========================================================================

# Create hashtag-account network from data:
# F = hashtag_network(DataCollection)

# ============================================
# Reduce the network by eliminating isolated or dead-end nodes
# F_red = reduce_network(F)

# ============================================
# Gephi export:
# nx.write_gexf(F, "twitterverse.gexf")

# ============================================
# Draw the network:
# nx.draw_spring(F)

# ============================================
# Draw degree histogram
# deg_histogram(F)


    

# TWEET TEMPORAL ANALYSIS
# ===========================================================================

# Plot Daily Tweets
# plot_dailytweets(DataCollection,names)

# ============================================
# Plot Retweet Ratio
# plot_retweetratio(DataCollection, names)

# ============================================
# Plot the Power Spectral Density 
# plot_PSD(DataCollection,names)


# ============================================
# get a list of tweets and retweets
# n = 'HAZ'
# tweets =  DataCollection[n].list_tweets()
# retweets = DataCollection[n].list_tweets(content="retweets")




# TEXT ANALYSIS
# ===========================================================================

# Plot wordclouds
# plot_wordclouds(DataCollection,names)


# ============================================
# Plot tweet lengths
# plot_tweetlength(DataCollection, names)


# NEXT: Function, die "Kennzahlen" des Graphen, etc in ein Textdokument schreibt.
# NEXT: Script fürs Twitter-Auslesen aufräumen. Beides in das selbe Verzeichnis mergen.






