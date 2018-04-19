# -*- coding: utf-8 -*-
import numpy as np
import random
import sklearn_crfsuite
import nltk
#import sklearn
#import scipy
#import scipy.stats
import gensim
# In[]
with open('ner.txt') as f:
    content = f.readlines()


data = []
data1 = []
sent = []
num_sent = 0;
label=[]
label_sent = []
for content_data in content:
    if not content_data == '\n':
        d1 = content_data.strip()
        d2 = d1.split()
        sent.append(d2[0])
        label_sent.append(d2[1])
    else:
        data1.append(sent)
        sent = nltk.pos_tag(sent)
        data.append(sent)
        label.append(label_sent)
        sent = []
        label_sent = []
        num_sent = num_sent + 1

# In[]

model = gensim.models.Word2Vec(data1,min_count=1,size = 50)
## for correlating words
# Label has 3 classes, so 
# In[]

K = 3
from sklearn.cluster import KMeans
embeddings = model[model.wv.vocab]
kmeans = KMeans(n_clusters=K)
kmeans.fit(embeddings)


assigned_cluster = []
for i in range(len(data1)):
    sent = model[data1[i]]
    assigned_cluster.append(kmeans.predict(sent))



# In[]

def word2features(sent, cluster_sent,i):
    word = sent[i][0]
    postag = sent[i][1]
    cluster = cluster_sent[i]

    features = {
        'bias': 1.0,
        'word.lower()': word.lower(),
        'word[-3:]': word[-3:],
        'word[-2:]': word[-2:],
        'word.isupper()': word.isupper(),
        'word.istitle()': word.istitle(),
        'word.isdigit()': word.isdigit(),
        'postag': postag,
        'postag[:2]': postag[:2],
        'word2VecCluster': cluster,
    }
    if i > 0:
        word1 = sent[i-1][0]
        postag1 = sent[i-1][1]
        features.update({
            '-1:word.lower()': word1.lower(),
            '-1:word.istitle()': word1.istitle(),
            '-1:word.isupper()': word1.isupper(),
            '-1:postag': postag1,
            '-1:postag[:2]': postag1[:2],
        })
    else:
        features['BOS'] = True

    if i < len(sent)-1:
        word1 = sent[i+1][0]
        postag1 = sent[i+1][1]
        features.update({
            '+1:word.lower()': word1.lower(),
            '+1:word.istitle()': word1.istitle(),
            '+1:word.isupper()': word1.isupper(),
            '+1:postag': postag1,
            '+1:postag[:2]': postag1[:2],
        })
    else:
        features['EOS'] = True

    return features

# In[]
def sent2features(sent,cluster_data):
    return [word2features(sent,cluster_data, i) for i in range(len(sent))]



# In[]
num_train = int(np.floor(num_sent*0.7))
num_valid = int(np.floor(num_sent*0.1))
num_test = num_sent - num_train - num_valid

idx = list(range(num_sent))
random.shuffle(idx)
# In[]

train_data =[]
train_label =[]
valid_data = []
valid_label = []
test_data = []
test_label =[]
train_cluster = []
valid_cluster= []
test_cluster = []

for i in range(0,num_train):
    train_data.append(data[idx[i]])
    train_label.append(label[idx[i]])
    train_cluster.append(assigned_cluster[idx[i]])

for i in range(num_train,num_train+num_valid):
    valid_data.append(data[idx[i]])
    valid_label.append(label[idx[i]])
    valid_cluster.append(assigned_cluster[idx[i]])

for i in range(num_train+num_valid,num_train+num_valid+num_test):
    test_data.append(data[idx[i]])
    test_label.append(label[idx[i]])
    test_cluster.append(assigned_cluster[idx[i]])


# In[]
#X_train = [sent2features(s,c) for s in train_data and c in train_cluster]
X_train = []
for i in range(len(train_data)):
    X_train.append(sent2features(train_data[i],train_cluster[i]))

Y_train = train_label

# In[]

X_test = []
for i in range(len(test_data)):
    X_test.append(sent2features(test_data[i],test_cluster[i]))

Y_test = test_label
# In[]
##time
crf = sklearn_crfsuite.CRF(
    algorithm='lbfgs',
    c1=0.1,
    c2=0.1,
    max_iterations=100,
    all_possible_transitions=True
)
crf.fit(X_train, Y_train)

# In[]
Y_pred = crf.predict(X_test)


# In[]
from sklearn.metrics import classification_report


# In[]
# convert["O","D","T"] to [0,1,2]

dicts = {"O":0,"D":1,"T":2}

Y_test_dicts = []
Y_pred_dicts = []
for i in range(len(test_data)):
    Y_test_dicts  =  Y_test_dicts + ([dicts[s] for s in Y_test[i]])
    Y_pred_dicts  = Y_pred_dicts + ([dicts[s] for s in Y_pred[i]])

Y_test_dicts = np.array(Y_test_dicts)
Y_pred_dicts = np.array(Y_pred_dicts)

match_score = classification_report(Y_test_dicts,Y_pred_dicts)

