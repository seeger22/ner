import re
import json
from fastDamerauLevenshtein import damerauLevenshtein as dl

class BabyTrie:#baby version of Trie
    class TrieNode:#Node within a Trie
        def __init__(self,word=None):
            self.children={}#dictionary of TrieNodes
            self.markers=[]#list of markers/categories
            self.end=False#the Node is leaf, or end of word
            self.word=None#in case needed
            self.id=None
    
    def __init__(self):
        self.root=self.new_node()

    def new_node(self,word=None):
        #Creates TrieNode object with a given word
        return self.TrieNode(word)

    def insert(self,lst,cat,number):
        '''
        Given a list of words that make up a Named Entity and its category,
        inserts the Entity into the Trie.

        Note: the structure resembles a tree, i.e. words as nodes, and at the end
        of the inserted word, the node is made a leaf node (end=True), and a Marker
        is added to the node's list of markers.
        -------------------------------------------------------------------
        Example:
        bt=BabyTrie()
        possible_NE=['Jade','Garden']#let's say that this is a restaurant and id#1
        bt.insert(possible_NE,'restaurant',1)
        '''
        if len(lst) == 0:
            print("ERROR: empty NE in knowledge file")
            return
        if len(lst) == 1 and lst[0]==cat:
            print("only one elem in lst")
            return
        #notice 'the' part is deleted here for dstc10 tuning
        if lst[-1]!=cat: #['a','and','b'] + ['restaurant']
            lst.append(cat)
        '''
        for the sake of more possible matches:
        If inserted "Jade Garden" and it's a restaurant,
        "Jade Garden" will be recognized as an entity;
        and "Jade Garden Restaurant" will also be one.
        '''
        ptr=self.root
        for i in range(0,len(lst)-1):#for every elem but not the last (since it is the category)
            if lst[i] not in ptr.children.keys():#if already a key, skip; else add new
                new=self.new_node(lst[i])
                ptr.children[lst[i]]=new
            ptr=ptr.children[lst[i]]
        if (len(lst)==2 and lst[-2] in ['good','ask']):#we dont want to treat good or ask as an entity (see test.txt)
            ptr.end=False
        elif (len(lst)==3 and lst[-3]=='cable' and lst[-2]=='car'):
            ptr.end=False
        else:
            ptr.end=True#is end of word
            ptr.id=number
        if cat not in ptr.markers:#Only adds new categories to the list of markers 
            ptr.markers.append(cat)
        if lst[-1] not in ptr.children.keys():#avoid possible conflict with same name
            new=self.new_node(lst[-1])
            ptr.children[lst[-1]]=new#adds the category as one of the leaf node
        ptr=ptr.children[lst[-1]]
        ptr.end=True
        ptr.id=number
        if cat not in ptr.markers:#only adds category if not in list of markers
            ptr.markers.append(cat)
    
    def isinTrie(self,sen):
        dic={}#the uncleaned version of returned dictionary
        flag=False#=True when a phrase in the sentence does not match the trie anymore
        lst=[]#the list that will ultimately be returned
        new_sen=sen.lower().strip()#cleans up sentence
        plst=re.findall(r"[\w']+|[.,!?;]", new_sen)#premature list used for clean-up
        p=re.compile(r"^(\w+)(\'\w+)$")
        for i in range (len(plst)):
            if p.match(plst[i]):
                new_word1,new_word2=p.match(plst[i]).group(1),p.match(plst[i]).group(2)
                lst.append(new_word1)
                lst.append(new_word2)
            else:
                lst.append(plst[i])
        
        #the returned list is completely formed at this point, we use it to generate dictionary
        rstart=0#starting position of NE
        rend=0#ending position of NE
        last=len(lst)-1#keep track of last to ensure index does not go over limit

        proceed=False
        for i in range(len(lst)):
            ptr=self.root
            if lst[i] in ptr.children:
                proceed=True
                rstart=i
                ptr=ptr.children[lst[i]]
            elif lst[i] not in ptr.children:
                for word in ptr.children:
                    if len(word)<=4:
                        dl_score=dl(lst[i],word,similarity=False,deleteWeight=2,insertWeight=2,replaceWeight=2)
                        bm=1
                    else:
                        dl_score=dl(lst[i],word,similarity=False,replaceWeight=2)
                        bm=2
                    if dl_score<=bm:
                        #print('for: ',lst[i],' and ',word,' edit distance: ',dl_score)
                        proceed=True
                        rstart=i
                        ptr=ptr.children[word]
                        break
            if proceed:
                for j in range(i+1,len(lst)):
                    if lst[j] in ptr.children:
                        ptr=ptr.children[lst[j]]
                        rend=j
                    elif lst[j] not in ptr.children:
                        proceed=False
                        for word in ptr.children:
                            if len(word)<=4:
                                dl_score=dl(lst[j],word,similarity=False,deleteWeight=2,insertWeight=2,replaceWeight=2)
                                bm=1
                            else:
                                dl_score=dl(lst[j],word,similarity=False,replaceWeight=2)
                                bm=2
                            if dl_score<=bm:
                                #print('for: ',lst[j],' and ',word,' edit distance: ',dl_score)
                                ptr=ptr.children[word]
                                rend=j
                                proceed=True
                                break
                        if not proceed:
                            rend=j-1
                            break
            if ptr.end:
                for i in range(len(ptr.markers)):
                    if (ptr.markers[i] in dic):#if already a key, add to value
                        if rstart>rend:
                            rend=rstart
                        dic[ptr.markers[i]].append((rstart,rend))
                    else:#if not, make new entry
                        if rstart>rend:
                            rend=rstart
                        dic[ptr.markers[i]]=[(rstart,rend)]
                rstart=0
                rend=0
            else:
                continue

        #cleaning up dictionary
        rdic={}#clean version of the dictionary that is ultimately returned
        for cat in dic.keys():
            rdic[cat]=[]
            rlst=sorted(dic[cat],key=lambda item:item[1]-item[0],reverse=True)
            #rdic[cat].append(rlst[0])
            for i in range(0,len(rlst)):
                rflag=True
                for rcat in rdic.keys():#make sure no overlap: ex. 'some hotel diner' > 'some hotel'
                    for elem in rdic[rcat]:
                        if (rlst[i][0]<elem[0] and rlst[i][1]<elem[0]):#ex. if we have (3,5) we can take (1,2)
                            continue
                        elif (rlst[i][0]>elem[1] and rlst[i][1]>elem[1]):#ex. if we have (3,5) we can take (6,7)
                            continue
                        else:# any equals, [0] or [1] will not work: ex. we have (3,5). cannot have (3,4) or (4,5).
                            if rlst[i][1]-rlst[i][0]==elem[1]-elem[0] and rlst[i][1]>elem[1]:
                                rdic[rcat].remove(elem)
                                continue
                            else:
                                rflag=False
                if rflag:
                    rdic[cat].append(rlst[i])
        del_lst=[]#cheap(costly) way to deal with empty dic entry
        for cat in rdic:
            if len(rdic[cat])==0:
                del_lst.append(cat)
        for elem in del_lst:
            del rdic[elem]
        return (lst,rdic)
        
    def initialize(self,dic):
        for cat in dic.keys():
            for elem in dic[cat]:
                record = dic[cat][elem]

                if ('name' in record and record['name'] is not None):
                    new_name=record['name'].lower().strip()#cleans up name
                    if new_name == cat:
                        print('exceptional entity---------------------')
                        continue
                    lst=[]#final list that is used to insert into bt
                    plst=re.findall(r"[\w']+|[&.,!?;]", new_name)#premature list, can have ex. "McDonald's" instead of "McDonald" and "'s"
                    p=re.compile(r"^(\w+)(\'\w+)$")

                    for i in range (len(plst)):
                        if p.match(plst[i]):
                            new_word1,new_word2=p.match(plst[i]).group(1),p.match(plst[i]).group(2)
                            lst.append(new_word1)
                            lst.append(new_word2)
                        else:
                            lst.append(plst[i])
                    #print(lst,cat,elem,sep='\n')
                    self.insert(lst,cat,elem)
                    for i in range(len(lst)):#& <=> and
                        if lst[i]=='&':
                            lst[i]='and'
                            self.insert(lst,cat,elem)
                        elif lst[i]=='and':
                            lst[i]='&'
                            self.insert(lst,cat,elem)

def main():
    k=open('knowledge_mod.json','r')
    dic=json.load(k)

    bt=BabyTrie()
    bt.initialize(dic)#setting up bt based on knowledge base
    
    res=bt.isinTrie('acron gest horse')
    print(res)
    k.close()