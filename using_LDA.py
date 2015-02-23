__author__ = 'simranjitsingh'

import math
import re
from nltk.corpus import stopwords
import csv
from gensim import corpora, models, similarities
from gensim.models import hdpmodel, ldamodel, LdaModel
from nltk.corpus import stopwords
import sqlite3


db = sqlite3.connect('nsf.db')

db.text_factory = str
cursor = db.cursor()
cursor.execute("delete from lda_topic")
db.commit()
#cursor.execute("create table lda_topic (word text, score text, topic_number integer)")

count_2014 = 0
count_2013 = 0
count_2012 = 0
mylist_2014=[]
exclude_words = ['investigate','experience','use','br']

with open('NSFdata.csv','rb') as f:
    reader = csv.reader(f)
    for row in reader:
            date = row[4]
            rev_date = date[::-1]
            rev_year = rev_date[0:4]

            year = rev_year[::-1]

            if year == '2014':
#                print row[24]
                content_2014 = row[24]
                content_2014 = content_2014.lower()

                words = re.findall(r'\w+', content_2014,flags = re.UNICODE | re.LOCALE)

                #This is the simple way to remove stop words
                important_words_2014=[]
                for word in words:
                     if word not in stopwords.words('english'):
                        if word not in exclude_words:
                            important_words_2014.append(word)
                important_string_2014 = str(important_words_2014)
                important_string_2014 = important_string_2014.replace("'", "")
                important_string_2014 = re.sub(" \d+", "", important_string_2014)
                important_string_2014 = important_string_2014.replace(",", "")
                mylist_2014.append(important_string_2014)
                count_2014 = count_2014+1


documents = mylist_2014


texts = [[word for word in document.lower().split() if word not in stopwords.words('english')]
         for document in documents]



all_tokens = sum(texts, [])
tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
texts = [[word for word in text if word not in tokens_once]
         for text in texts]


dictionary = corpora.Dictionary(texts)
corpus = [dictionary.doc2bow(text) for text in texts]

lda = LdaModel(corpus, id2word=dictionary, num_topics=10)

#print lda.print_topics(num_words=100,num_topics=10)

for i in range(0, lda.num_topics):
    print lda.print_topic(i)
    string_topic = lda.print_topic(i)
    topic_words = re.findall(r'\b[a-z]+\b',string_topic)
    word_score = re.findall(r'0.\d+',string_topic)
    tp_number = i + 1
    index = 0
    while index < len(topic_words):
        cursor.execute("insert into lda_topic(word,score,topic_number) values (?,?,?)", (topic_words[index],word_score[index],tp_number,))
        index = index + 1

db.commit()

