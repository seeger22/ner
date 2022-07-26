import re

class BabyTrie:#baby version of Trie
    class TrieNode:#Node within a Trie
        def __init__(self,word=None):
            self.children={}#dictionary of TrieNodes
            self.markers=[]#list of markers/categories
            self.end=False#the Node is leaf, or end of word
            self.word=word#in case needed
    
    def __init__(self):
        self.root=self.new_node()

    def new_node(self,word=None):
        #Creates TrieNode object with a given word
        return self.TrieNode(word)

    def insert(self,lst,cat):
        '''
        Given a list of words that make up a Named Entity and its category,
        inserts the Entity into the Trie.

        Note: the structure resembles a tree, i.e. words as nodes, and at the end
        of the inserted word, the node is made a leaf node (end=True), and a Marker
        is added to the node's list of markers.
        -------------------------------------------------------------------
        Example:
        bt=BabyTrie()
        possible_NE=['Jade','Garden']#let's say that this is a restaurant
        bt.insert(possible_NE,'restaurant')
        '''
        if len(lst) == 0:
            print("ERROR: empty NE in knowledge file")
            return
        if len(lst) == 1 and lst[0]==cat:
            print("only one elem in lst")
            return
        if lst[0]=='the':
            lst.pop(0)#'the' is ambiguous in many cases, so it's best to just discard it from part of an entity
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
        if cat not in ptr.markers:#Only adds new categories to the list of markers 
            ptr.markers.append(cat)
        if lst[-1] not in ptr.children.keys():#avoid possible conflict with same name
            new=self.new_node(lst[-1])
            ptr.children[lst[-1]]=new#adds the category as one of the leaf node
        ptr=ptr.children[lst[-1]]
        ptr.end=True
        if cat not in ptr.markers:#only adds category if not in list of markers
            ptr.markers.append(cat)
    
    def isinTrie(self,sen):
        '''
        Given a sentence/string,
        returns a tuple ((1),(2)) where:
                 (1) is a list of the stripped, lowercased, and split (even punctuations)
        sentence, mainly for the convenience of tokenization.
                 (2) is a dictionary with keys as categories and their values as tuples where
        the first index is the starting position and second index is the ending position
        of the Named Entities in the sentence.

        Note: these Named Entities are defined on the BabyTrie.
        Note also:
        1. While doing the clean-up for the sentence, if given string is "McDonald's" or anything
        with RE structure ^(\w+)(\'w+)$ will be split as (\w+) and (\'w+), i.e. "McDonald" and "'s"
        2. While cleaning up the dictionary for output, the longest instance is always taken.
        A node can also have multiple markers, in the case where both instances happen and have
        the same exact distances, both will be counted towards the final result. For further
        information please see the comment for each condition and the final output.
        -------------------------------------------------------------------------------------
        Example:
        #bt is already defined in the above example, which has an inserted entity
        test_sentence='I went to Jade Garden last night.'
        res=bt.isinTrie(test_sentence)
        print(res[0],'\n',res[1])

        Output:
        ['i','went','to','jade','garden','last','night','.']
        {'restaurant':(3,4)}
        '''
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

        for i in range (len(lst)):
            ptr=self.root
            if lst[i] in ptr.children:
                rstart=i
                ptr=ptr.children[lst[i]]
                for j in range (i+1,len(lst)):
                    if lst[j] not in ptr.children:
                        flag=True
                        rend=j-1
                        break
                    ptr=ptr.children[lst[j]]
                    rend=j
                
                if ptr.end:
                    for i in range(len(ptr.markers)):
                        if (ptr.markers[i] in dic):#if already a key, add to value
                            dic[ptr.markers[i]].append((rstart,rend))
                        else:#if not, make new entry
                            dic[ptr.markers[i]]=[(rstart,rend)]
                    rstart=0
                    rend=0

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
        return (lst,rdic)