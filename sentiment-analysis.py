from nltk.parse.stanford import StanfordDependencyParser
from nltk import RegexpParser, word_tokenize, pos_tag
from nltk.tag.stanford import StanfordPOSTagger
from nltk.corpus import sentiwordnet as swn
from nltk.corpus import wordnet

# blm handle kalo katanya sama dalam kalimat
# blm handle detect conjunction between clause
# blm handle check aspect

def getSentiment(word):
	sentimentScore = sentiments[word]["score"][0]
	if(sentimentScore == 0 and sentiments[word]["visited"][0]==0):
		sentiments[word]["visited"][0] = 1
		sentimentScore = checkSentiment(word)
		sentimentScore += check1(word)
		if(sentimentScore == 0):
			sentimentScore = check2(word)
			if(sentimentScore == 0):
				sentimentScore = check3(word)
	sentiments[word]["score"][0] += sentimentScore
	return sentimentScore

# check relation nsubj, amod, nmod, dobj, conj 
def check1(word):
	sentimentScore = 0
	for r in relation[word]:
		if r[0] in ['nsubj', 'amod', 'nmod'] and r[1] in pos['JJ']:
			sentimentScore += checkSentiment(r[1])
		if r[0] == 'dobj':
			sentimentScore += checkSentiment(r[1])
	return sentimentScore

# check relation with JJ
def check2(word):
	sentimentScore = 0
	for r in relation[word]:
		if r in pos['JJ']:
			sentimentScore += checkSentiment(r[1])
	return sentimentScore

# check the neighbors 
def check3(word):
	sentimentScore=0
	for r in relation[word]:
		sentimentScore += getSentiment(r[1])
	if sentimentScore == 0:
		for r in relation[word]:
			if sentiments[r[1]]["visited"][0]==0:
				sentimentScore += check3(r[1])
	return sentimentScore

# check sentiment from sentiword 
def checkSentiment(word):
	if sentiments[word]["pos"][0] not in ['DT','IN']:
		if 0 in sentiments[word]["score"]:
			pos = getWordnetPos(sentiments[word]["pos"][0])
			for x in range(1,3):
				try:
					res = swn.senti_synset('%s.%s.%s' % (word, pos,"0"+str(x)))
					d = res.pos_score() - res.neg_score()
					if d != 0:
						sentiments[word]["score"][0] = d
						break
				except:
					pass
	return sentiments[word]["score"][0]

def getWordnetPos(tag):
  if tag.startswith('J'):
      return wordnet.ADJ
  elif tag.startswith('V'):
      return wordnet.VERB
  elif tag.startswith('N'):
      return wordnet.NOUN
  elif tag.startswith('R'):
      return wordnet.ADV
  else:
      return wordnet.NOUN # or None or ''

# check conjunction
def checkConj(word):
	sentimentScore = 0
	count=0
	for k in relation[word]:
		if k[0] == "conj":
			# cek if there is "and" between them
			if "and" in sentiments:
				for i in sentiments['and']["position"]:
					if (sum(p > i for p in sentiments[word]["position"])>0 and sum(p < i for p in sentiments[k[1]]["position"])>0) or (sum(p < i for p in sentiments[word]["position"])>0 and sum(p > i for p in sentiments[k[1]]["position"])>0):
						sentimentScore += sentiments[k[1]]["score"][0]
	sentiments[word]["score"][0] += sentimentScore
	return sentimentScore

def checkAspect(word): # --please complete this--
	return 1

# Extract sentence
sentence = "Sound is crystal clear and the bass is very deep as well "

# Detect noun phrase
grammar = r"""
  NP: {<DT|PP\$>?<JJ>*<NN|NNS|NNP>+}   # chunk determiner/possessive, adjectives and noun
      {<NNP>+}                # chunk sequences of proper nouns
"""
cp = RegexpParser(grammar)
path_to_model = "stanford-postagger-2015-04-20/models/english-bidirectional-distsim.tagger"
path_to_jar = "stanford-postagger-2015-04-20/stanford-postagger.jar"
st = StanfordPOSTagger(path_to_model, path_to_jar)
postag = st.tag(sentence.split())
tree_result = cp.parse(postag)

# postag 
pos = {} # list of postag
pos['JJ']=[]
sentiments = {} # list of words contains pos, sentiment score, position, visited
count = 0
for p in st.tag(sentence.split()):
	pos.setdefault(p[1], []).append(p[0])
	sentiments.setdefault(p[0], {}).setdefault("pos", []).append(p[1])
	sentiments.setdefault(p[0], {}).setdefault("score", []).append(0)
	sentiments.setdefault(p[0], {}).setdefault("position", []).append(count)
	sentiments.setdefault(p[0], {}).setdefault("visited", []).append(0)
	count+=1

#extract only NP
nounPhrase = {}
nounPhrase['word'] = [subtree.leaves() for subtree in tree_result.subtrees() if subtree.label() == 'NP']
nounPhrase['score'] = []

# Detect conjunction --please complete this---
# if any and, check clause or not, if not, check sentiment 

# Dependency Parser
path_to_jar = 'stanford-parser-full-2016-10-31/stanford-parser.jar'
path_to_models_jar = 'stanford-parser-full-2016-10-31/stanford-parser-3.7.0-models.jar'
dependency_parser = StanfordDependencyParser(path_to_jar=path_to_jar, path_to_models_jar=path_to_models_jar)
result = dependency_parser.raw_parse(sentence)
dep = result.next()
relation =  {}
for p in dep.triples():
	relation.setdefault(p[0][0], []).append((p[1],p[2][0],1))
	relation.setdefault(p[2][0], []).append((p[1],p[0][0],-1))

# Sentiment Analysis
count = 0
for p in nounPhrase['word']:
	sentimentScore=0
	for i in p:
		if(i[1] in ['NN','NNP','NNS']):
			score = getSentiment(i[0])
			sentimentScore += score
	nounPhrase['score'].append(sentimentScore)
	count+=1

# check conj relation
count=0
for p in nounPhrase['word']:
	sentimentScore=0
	for i in p:
		if(i[1] in ['NN','NNP','NNS']):
			if sentiments[i[0]]["score"][0] == 0:
				sentimentScore += checkConj(i[0])
				nounPhrase['score'][count]=sentimentScore
	count+=1

# print aspect and sentiment score
count=0
for p in nounPhrase["word"]:
	if nounPhrase["score"][count] != 0:
		print "%s%s%s" % (p, " ", str(nounPhrase["score"][count]))

# for r in relation:
# 	print r,relation[r]