import re
import os
import json
import string
from torch.utils.data import Dataset

import nltk
from nltk.stem.snowball import SnowballStemmer
nltk.download('stopwords')
from nltk.corpus import stopwords

class KnowledgeDataset(Dataset):
  """
  Yield delexicalized title utterances
  """
  def __init__(self, dataroot, filename, tokenizer, title_field='title_ex', body_field='body_ex'):
    path = os.path.join(os.path.abspath(dataroot))
    
    kb_file = os.path.join(path, filename)
    with open(kb_file, 'r') as f:
      self.kb = json.load(f)

    self.ps = SnowballStemmer("english", ignore_stopwords=True)
    self.stopwords = stopwords.words('english')

    self.kid2doc = {}
    self.kb_utterances = {}
    self.kb_utterances_list = []

    # remove stopwords, sort remaining keywords on title
    self.kb_utterances1 = {}
    self.kb_utterances_list1 = []

    # remove stopwords, sort remaining keywords on body
    self.kb_utterances2 = {}
    self.kb_utterances_list2 = []

    self.entity_utterances = {}

    for domain in self.kb.keys():
      self.entity_utterances[domain] = []
      for i, entity in self.kb[domain].items():
        name = entity["name"]
        titles = []
        for j, qa, in entity["docs"].items():
          kid = "{}_{}_{}".format(domain, i, j)
          # Use title_template first. If not found, use the default title
          title = qa[title_field] if title_field in qa else qa["title_template"]
          body = qa[body_field] if body_field in qa else qa["body_template"]

          self.kid2doc[kid] = title + "\t" + body

          q = self.delexicalize(domain, name, title)
          q1 = self.norm_query(q)

          a = self.delexicalize(domain, name, body)
          a1 = self.norm_query(a)

          titles.append(q)

          if q not in self.kb_utterances:
            self.kb_utterances[q] = [kid]
            # only store uniq query
            self.kb_utterances_list.append(q)
          else:
            self.kb_utterances[q].append(kid)
            
          if q1 not in self.kb_utterances1:
            self.kb_utterances1[q1] = [kid]
            # only store uniq query
            self.kb_utterances_list1.append(q1)
          else:
            self.kb_utterances1[q1].append(kid)

          if a1 not in self.kb_utterances2:
            self.kb_utterances2[a1] = [kid]
            # only store uniq query
            self.kb_utterances_list2.append(a1)
          else:
            self.kb_utterances2[a1].append(kid)

        self.entity_utterances[domain].append(titles)
    self.tokenizer = tokenizer

    # merge equivalent entity docs in kb_utterances1 and kb_utterances2 
    self.doc2clusterIdx = {}
    self.doc_clusters = []
    num_cluster = 0

    # get the doc subsets
    for S in self.kb_utterances1.values():
      # check if any docid exists in current map
      c = None
      for docid in S:
        if docid in self.doc2clusterIdx:
          c = self.doc2clusterIdx[docid]
          break
      if c is None:
        # create new cluster idx c
        c = num_cluster
        num_cluster += 1
        self.doc_clusters.append(set({}))
      # add all docid into c
      for docid in S:
        self.doc2clusterIdx[docid] = c
        self.doc_clusters[c].add(docid)
        
    self.doc2clusterIdx2 = {}
    self.doc_clusters2 = []
    num_cluster2 = 0

    # get the doc subsets
    for S in self.kb_utterances2.values():
      # check if any docid exists in current map
      c = None
      for docid in S:
        if docid in self.doc2clusterIdx2:
          c = self.doc2clusterIdx2[docid]
          break
      if c is None:
        # create new cluster idx c
        c = num_cluster2
        num_cluster2 += 1
        self.doc_clusters2.append(set({}))
      # add all docid into c
      for docid in S:
        self.doc2clusterIdx2[docid] = c
        self.doc_clusters2[c].add(docid)

    # merge set 2
    for S in self.kb_utterances2.values():
      # check if any docid exists in current map
      cluster_set = {}
      for docid in S:
        if docid in self.doc2clusterIdx:
          c = self.doc2clusterIdx[docid]
          # keep count. We only trust count > 1 (multiple docids from body map to the same title cluster)
          if c in cluster_set:
            cluster_set[c] += 1
          else:
            cluster_set[c] = 1

      # now we should merge all docs in cluster_set into a new cluster index
      new_cluster = set({})
      for i in cluster_set.keys():
        # only trust merging clusters with count > 1
        if cluster_set[i] <= 1:
          continue
        for docid in self.doc_clusters[i]:
          # update docid to the new cluster idx
          self.doc2clusterIdx[docid] = num_cluster
          new_cluster.add(docid)
        # clear i
        self.doc_clusters[i] = set({})

      # discard the body cluster due to potential noise
      #for docid in S:
      #  self.doc2clusterIdx[docid] = num_cluster
      #  new_cluster.add(docid)

      self.doc_clusters.append(new_cluster)
      num_cluster += 1

    # remove singleton clusters
    self.doc_clusters = [c for c in self.doc_clusters if len(c) > 0]
    self.doc_clusters2 = [c for c in self.doc_clusters2 if len(c) > 0]

  def get_doc(self, kid):
    try:
      return self.kid2doc[kid]
    except:
      return "Not found"

  def norm_query(self, query):
    """
    remove stopwords, stem each word, sort the word order, remove punctuation
    """
    query = query.lower()
    # remove anything after
    #query = re.sub(r"this \w+", "", query)
    #query = re.sub(r"this restaurant", "", query)
    #query = re.sub(r"this attraction", "", query)
    #query = re.sub(r"this facility", "", query)
    #query = re.sub(r"this property", "", query)
    #query = re.sub(r"this location", "", query)
    #query = re.sub(r"this site", "", query)
    #query = re.sub(r"this place", "", query)
    #query = re.sub(r"this spot", "", query)
    tokens = query.split()
    tokens = [self.ps.stem(w) for w in tokens if w not in self.stopwords]
    tokens = [w.translate(str.maketrans('', '', string.punctuation)) for w in tokens]
    tokens = [self.ps.stem(w) for w in tokens if w not in self.stopwords]
    return " ".join(sorted(tokens))
  
  def delexicalize(self, domain, name, query):
    """
    Replace occurrence of entity in sentence by domain
    For example: domain = 'hotel', name = 'A and B Guest House'
    Can I bring my pet to A and B Guest House? -> Can I bring my pet to this hotel?
    """
    # TODO: Need Trie here for fast entity matching
    return query

  def __iter__(self):
    for q in self.kb_utterances_list:
      yield q

  def __getitem__(self, index):
    return self.kb_utterances_list[index]

  def __len__(self):
    return len(self.kb_utterances_list)

  def save(self, out_file):
    with open(out_file, 'w') as f:
      for q in self.kb_utterances_list:
        f.write("{}\n".format(q))

  def collate_fn(self, batch):
    """
    Received a batch of queries.
    Return: dictionary of inputs
    """
    output = self.tokenizer(batch, padding=True, add_special_tokens = True, return_tensors="pt")
    output_dict = {x: output[x].to(device) for x in output}
    output_dict["query"] = batch

    return output_dict