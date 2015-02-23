from __future__ import division

__author__ = 'simranjitsingh'

import math
from textblob import TextBlob as tb
import re
from nltk.corpus import stopwords
import collections
from collections import Counter
import csv
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from contextlib import closing
import os
from flask import Flask, request, redirect, url_for, render_template
from werkzeug import secure_filename
import re
import sqlite3
import csv
from pytagcloud import create_tag_image, make_tags, LAYOUT_HORIZONTAL, LAYOUT_MOST_HORIZONTAL , LAYOUT_MIX
from pytagcloud.lang.counter import get_tag_counts
import matplotlib.pyplot as plt; plt.rcdefaults()
import random

print_msg = ""
UPLOAD_FOLDER = 'C:\Users\simranjitsingh\PycharmProjects\DIA2_dashboard'
ALLOWED_EXTENSIONS = set(['csv'])

db = sqlite3.connect('nsf.db')

db.text_factory = str
cursor = db.cursor()

app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def getplot(filename,xdata,ydata):
    gap_list = []
    for index in range(0,len(xdata)):
        each_gap = 2 * index
        gap_list.append(each_gap)
    performance = ydata
    fig = plt.figure()
    plt.bar(gap_list, performance, align='center', alpha=0.6)

    plt.xticks(gap_list, xdata)
    gap_list = []
    plt.ylabel('Number of Documents')
    plot_title = "Top words in year: " + filename[:4]
    plt.title(plot_title)

    fig.autofmt_xdate()
#    filename = filename + '.png'
    file_path = os.path.join('static',filename)
    return plt.savefig(file_path,format="png")

def tf(word, blob):
    return blob.words.count(word) / len(blob.words)

#returns the number of documents containing word
def n_containing(word, bloblist):
    return sum(1 for blob in bloblist if word in blob)

#computes "inverse document frequency" which measures how common a word is
#among all documents in bloblist. The more common a word is, the lower its idf.
# We take the ratio of the total number of documents to the number of documents
# containing word, then take the log of that. Add 1 to the divisor to prevent
# division by zero.
def idf(word, bloblist):
    return math.log(len(bloblist) / (1 + n_containing(word, bloblist)))

#computes the TF-IDF score
def tfidf(word, blob, bloblist):
    return tf(word, blob) * idf(word, bloblist)


def compute():
    cursor.execute("delete from hot_topics")
    exclude_words = ['investigate','experience','use','br']
    year_span = ['2011','2012','2013','2014']
    no_of_years = len(year_span)
    year_data = dict()
    year_data_bigram = dict()
    temp_list=[]
    for i in year_span:
        cursor.execute('select * from nsf_data where years =?',(i,))
        for row in cursor:
                content_2014 = row[3]
                content_2014 = content_2014.lower()

                words = re.findall(r'\w+', content_2014,flags = re.UNICODE | re.LOCALE)

                #This is the simple way to remove stop words
                important_words_2014=[]
                for word in words:
                     if word not in stopwords.words('english'):
                        if word not in exclude_words:
                            important_words_2014.append(word)
                for x in range(len(important_words_2014)-1):
                    bigram = important_words_2014[x] + '-' + important_words_2014[x+1]
                    temp_list.append(bigram)

                temp_var = str(temp_list)

                temp_var = temp_var.replace(",", "")
                temp_var = temp_var.replace("'", "")
                temp_var = re.sub(" \d+", "", temp_var)
                temp_var = temp_var.replace("[", "")
                temp_var = temp_var.replace("]", "")

                del temp_list[:]

                important_string_2014 = str(important_words_2014)
                important_string_2014 = important_string_2014.replace("'", "")
                important_string_2014 = re.sub(" \d+", "", important_string_2014)
                important_string_2014 = important_string_2014.replace(",", "")

                if i in year_data:
                    year_data[i].append(important_string_2014)
                else:
                    year_data[i] = [important_string_2014]

                if i in year_data_bigram:
                    year_data_bigram[i].append(temp_var)
                else:
                    year_data_bigram[i] = [temp_var]

    j = 0
    for key,value in year_data.items():
        while j < len(value):
            value[j] = tb(value[j])
            j = j + 1
        j = 0
    j1 = 0
    for key,value in year_data_bigram.items():
        while j1 < len(value):
            value[j1] = tb(value[j1])
            j1 = j1 + 1
        j1 = 0

    disp_dict=dict()
    disp_dict_bigram = dict()

    for years,contents in year_data.items():
        bloblist = contents
 #       print years

        for i, blob in enumerate(bloblist):
#            print("Top words in document {}".format(i + 1))
            scores = {word: tfidf(word, blob, bloblist) for word in blob.words}

            sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)

            for word, score in sorted_words[:5]:
#                print("Word: {}, TF-IDF: {}".format(word, round(score, 5)))
                if years in disp_dict:
                    disp_dict[years].append(word)
                else:
                    disp_dict[years] = [word]

    for years,contents_bigram in year_data_bigram.items():
        bloblist = contents_bigram
 #       print years

        for i, blob in enumerate(bloblist):
#            print("Top words in document {}".format(i + 1))
            scores = {word: tfidf(word, blob, bloblist) for word in blob.words}

            sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)

            for word, score in sorted_words[:5]:
#                print("Word: {}, TF-IDF: {}".format(word, round(score, 5)))
                if years in disp_dict_bigram:
                    disp_dict_bigram[years].append(word)
                else:
                    disp_dict_bigram[years] = [word]


    for key,value in disp_dict.items():
            c = collections.Counter(value)
            for letter1, count1 in c.most_common(20):
                letter1 = letter1.upper()
                cursor.execute("insert into hot_topics(word,year,docs) VALUES(?,?,?)",(letter1,key,count1))

    for key,value in disp_dict_bigram.items():
            c = collections.Counter(value)
            for letter1, count1 in c.most_common(20):
                letter1 = letter1.upper()
                cursor.execute("insert into hot_topics(word,year,docs) VALUES(?,?,?)",(letter1,key,count1))

    db.commit()

    send_message = "Calculation Done"
    return send_message

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/')
def show_data():
    year_list = []
    cloud_tag = []
    bar_images = []
    cursor.execute('select word,year,docs from hot_topics order by docs desc ')
    entries = [dict(word=row[0], year=row[1], docs=row[2]) for row in cursor.fetchall()]
    cursor.execute('select distinct(year) from hot_topics')
    for row in cursor:
        year_list.append(row[0])
    cursor.execute('select word,docs from hot_topics order by docs DESC LIMIT 20 ')
    top_list = [dict(word=row[0], docs=row[1]) for row in cursor.fetchall()]
    cursor.execute('select * from nsf_data order by RANDOM() LIMIT 5')
    top_data = [dict(topic=row[1], docs=row[3]) for row in cursor.fetchall()]
    cursor.execute('select new_image_name from images where plot_type = ?',('cloud',))
    for row in cursor:
        word_cloud =  row[0]
    cursor.execute('select new_image_name from images where plot_type = ?',('bar',))
    for row in cursor:
        bar_images.append(row[0])


    return render_template('index.html',entries=entries,year_list=year_list,top_list=top_list,top_data=top_data,word_cloud=word_cloud,bar_images=bar_images)



@app.route('/file')
def show_file():
    global print_msg
    return render_template('forms.html',print_msg=print_msg)

@app.route('/charts')
def show_chart():
    bar_images=[]
    cursor.execute('select new_image_name from images where plot_type = ?',('bar',))
    for row in cursor:
        bar_images.append(row[0])
    return render_template('morris.html',bar_images=bar_images)

@app.route('/addfile', methods=['GET', 'POST'])
def upload_file():

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            only_name = filename.rsplit('.', 1)
            fname = only_name[0]
            ext = only_name[1]
            changed_name = fname + '1.' + ext
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], changed_name))
            db = sqlite3.connect('nsf.db')
            db.text_factory = str
            cursor = db.cursor()
            cursor.execute("delete from nsf_data")
#            cursor.execute("begin")
            aaa = str(changed_name)
            with open(aaa,'rb') as f:
                reader = csv.reader(f)
                for row in reader:
                    date = row[4]
                    rev_date = date[::-1]
                    rev_year = rev_date[0:4]
                    year = rev_year[::-1]
                    content = row[24]
                    title = row[1]
                    cursor.execute("insert into nsf_data(title,years,doc) VALUES(?,?,?)",(title,year,content))
     #       cursor.execute('create table images(image_name TEXT NOT NULL , new_image_name TEXT NOT NULL , plot_type TEXT NOT NULL )')
            db.commit()
            global print_msg
            print_msg = "Data uploaded to the database"
            f.close()
            compute()
            year_list = []
            cursor.execute('select distinct(year) from hot_topics')
            for row in cursor:
                year_list.append(row[0])

            cursor.execute('select word,year,docs from hot_topics order by docs DESC ')
            entries = [dict(word=row[0], year=row[1], docs=row[2]) for row in cursor.fetchall()]

            cloud_tag = []
            cursor.execute('select word from hot_topics order by docs DESC LIMIT 20 ')
            for row in cursor:
                cloud_tag.append(row[0])

            str1 = str(cloud_tag)
            str1 = str1.replace(",","")
            str1 = str1.replace("'","")
            str1 = str1.replace("[","")
            str1 = str1.replace("]","")
            str1 = str1.replace("-","_")

            tags = make_tags(get_tag_counts(str1))
     #       cursor.execute('create table images(image_name TEXT NOT NULL , new_image_name TEXT NOT NULL , plot_type TEXT NOT NULL )')
            random_var = random.randint(1, 1000)
            list_doc = []
            list_word = []
            cursor.execute("delete from images")
            for time in year_list:
                plot_image_name = time + str(random.randint(1,1000)) + '.png'
                cursor.execute("insert into images(image_name,new_image_name,plot_type) VALUES(?,?,?)",(time,plot_image_name,'bar'))
                for i in entries:
                    if i['year'] == time:
                        doc_count = int(i['docs'])
                        list_doc.append(doc_count)
                        list_word.append(i['word'])
                getplot(plot_image_name,list_word[:20],list_doc[:20])
                list_doc = []
                list_word = []
            db.commit()
            image_name = 'cloud_image'


            image_name = image_name + str(random_var)
            image_name = image_name + '.png'

            image_path = os.path.join('static',image_name)

            create_tag_image(tags, image_path, size=(550, 200), layout=2, fontname='PT Sans Regular',)

            cursor.execute("insert into images(image_name,new_image_name,plot_type) VALUES(?,?,?)",('cloud_image',image_name,'cloud'))

            db.commit()

   #          cursor.execute('select * from nsf_data')
  #          for row in cursor:
  #              print row
    else:
        print_msg = ""
    return redirect(url_for('show_file'))





if __name__ == '__main__':
    app.run()
