import re
import json
from fastDamerauLevenshtein import damerauLevenshtein as dl
from num2words import num2words
from simple_tokenize import Clean_Text
from simple_tokenize import Word_Tokenize
from extra_methods import simple_num2words

class BabyTrie:#baby version of Trie
    class TrieNode:#Node within a Trie
        def __init__(self,entity=None):
            self.children={}#dictionary of TrieNodes
            self.markers=[]#list of markers/categories
            self.end=False#the Node is leaf, or end of word
            self.entity=None#in case needed
            self.id=None
    
    def __init__(self):
        self.root=self.new_node()

    def new_node(self,word=None):
        #Creates TrieNode object with a given word
        return self.TrieNode(word)

    def restricted_insert(self,lst,cat,number):
        if len(lst) == 0:
            print("ERROR: empty NE in knowledge file")
            return
        if len(lst) == 1 and lst[0]==cat:
            print("only one elem in lst")
            return
        
        if lst[0]=='the':#the is ambiguous
            lst.pop(0)

        ptr=self.root
        for i in range(0,len(lst)):#for every elem but not the last (since it is the category)
            if lst[i] not in ptr.children.keys():#if already a key, skip; else add new
                new=self.new_node(lst[i])
                ptr.children[lst[i]]=new
            ptr=ptr.children[lst[i]]
        #if (len(lst)==2 and lst[-2] in ['good','ask','page']):#we dont want to treat good or ask as an entity (see test.txt)
            #ptr.end=False
        if (len(lst)==3 and lst[-3]=='cable' and lst[-2]=='car'):
            ptr.end=False
        else:
            ptr.end=True#is end of word
            ptr.id=number
        if cat not in ptr.markers:#Only adds new categories to the list of markers 
            ptr.markers.append(cat)
    
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
        
        if lst[0]=='the':#the is ambiguous
            lst.pop(0)
        
        
        
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
        if (len(lst)==2 and lst[-2] in ['good','ask','page']):#we dont want to treat good or ask as an entity (see test.txt)
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
        stutter_match=False
        dl_mistakes=['train','want','american','lane','fees','fee','marina','wanna','canna','dinna','finna']
        #outfile for tracking log process
        dic={}#the uncleaned version of returned dictionary
        flag=False#=True when a phrase in the sentence does not match the trie anymore
        lst=[]#the list that will ultimately be returned

        new_sen=sen.lower().strip()#cleans up sentence

        lst=Word_Tokenize(Clean_Text(new_sen))
        
        last=len(lst)-1#keep track of last to ensure index does not go over limit
        #the returned list is completely formed at this point, we use it to generate dictionary
        rstart=0#starting position of NE
        rend=0#ending position of NE

        proceed=False
        for i in range(len(lst)):
            ptr=self.root
            if lst[i] in ptr.children:
                proceed=True
                rstart=i
                ptr=ptr.children[lst[i]]
            elif lst[i] not in ptr.children and lst[i] not in dl_mistakes:
                for word in ptr.children:
                    if len(lst[i])<=4:
                        dl_score=dl(lst[i],word,similarity=False,deleteWeight=2,insertWeight=2,replaceWeight=2)
                        bm=0
                    else:
                        dl_score=dl(lst[i],word,similarity=False,deleteWeight=1,insertWeight=2,replaceWeight=2)
                        bm=1
                    if dl_score<=bm:
                        proceed=True
                        rstart=i
                        ptr=ptr.children[word]
                        break
            if proceed:
                stutter_utt=0
                for j in range(i+1,len(lst)):
                    if lst[j] in ptr.children:
                        ptr=ptr.children[lst[j]]
                        rend=j
                        stutter_match=False
                    elif lst[j] not in ptr.children:
                        proceed=False
                        for word in ptr.children:
                            dl_score=dl(lst[j],word,similarity=False,deleteWeight=2,insertWeight=2,replaceWeight=2)
                            bm=1
                            if dl_score<=bm and lst[j].isalnum():
                                ptr=ptr.children[word]
                                rend=j
                                proceed=True
                                stutter_match=False
                                break
                        if (len(lst[j])<=3) and (lst[j].isalnum()) and (stutter_utt<1):#allow one mismatch (except for punc), could be stuttering
                            stutter_utt+=1
                            proceed=True
                            rend=j-1
                            stutter_match=True
                            #here rend not counted since if next is not matched, it will not be effected if the prev word is actually end of word
                        elif stutter_match:
                            rend=j-2
                            break
                        #print('for '+lst[i]+' stopped at '+lst[j])#degbug use
                        if not proceed:
                            rend=j-1
                            break

            if ptr.end:
                for i in range(len(ptr.markers)):
                    if (ptr.markers[i] in dic):#if already a key, add to value
                        if rstart>rend:
                            rend=rstart
                        dic[ptr.markers[i]].append(((rstart,rend),ptr.id))
                    else:#if not, make new entry
                        if rstart>rend:
                            rend=rstart
                        dic[ptr.markers[i]]=[((rstart,rend),ptr.id)]
                rstart=0
                rend=0
            else:
                continue
        #print(dic)
        #cleaning up dictionary
        rdic={}#clean version of the dictionary that is ultimately returned
        for cat in dic.keys():
            rdic[cat]=[]
            rlst=sorted(dic[cat],key=lambda item:item[0][1]-item[0][0],reverse=True)
            #rdic[cat].append(rlst[0])
            for i in range(0,len(rlst)):
                rflag=True
                for rcat in rdic.keys():#make sure no overlap: ex. 'some hotel diner' > 'some hotel'
                    for elem in rdic[rcat]:
                        if (rlst[i][0][0]<elem[0][0] and rlst[i][0][1]<elem[0][0]):#ex. if we have (3,5) we can take (1,2)
                            continue
                        elif (rlst[i][0][0]>elem[0][1] and rlst[i][0][1]>elem[0][1]):#ex. if we have (3,5) we can take (6,7)
                            continue
                        else:# any equals, [0] or [1] will not work: ex. we have (3,5). cannot have (3,4) or (4,5).
                            if rlst[i][0][1]-rlst[i][0][0]==elem[0][1]-elem[0][0] and rlst[i][0][1]>elem[0][1]:
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
        dig=False
        chain_entities={}#keeping track of chain restaurants' ids i.e. {'entity name':('cat','id1|id2|id3|...')}
        for cat in dic.keys():
            for elem in dic[cat]:
                record = dic[cat][elem]

                if ('name' in record and record['name'] is not None):
                    new_name=record['name'].lower().strip()#cleans up name
                    if new_name == cat:
                        print('exceptional entity---------------------')
                        continue
                    lst=[]#final list that is used to insert into bt
                    dlst=[]
                    plst=Word_Tokenize(Clean_Text(new_name))#need to go through dig process below

                    for i in range (len(plst)):
                        if plst[i].isnumeric():
                            dig=True
                            converted=num2words(plst[i])
                            if '-' in converted:
                                converted_lst=converted.split('-')
                                for digword in converted_lst:
                                    dlst.append(digword)
                            else:
                                converted_lst=converted.split()
                                for digword in converted_lst:
                                    dlst.append(digword)
                            lst.append(plst[i])
                            continue
                        else:
                            dig=False
                            lst.append(plst[i])
                            dlst.append(plst[i])

                    self.insert(lst,cat,elem)

                    if dig:
                        #print(dlst)
                        self.insert(dlst,cat,elem)

                    if '-' in lst:#chain rest: xxx - xxx
                        base_entity=' '.join(lst[0:lst.index('-')])
                        lst.remove('-')#we won't have these types of punc in logs. remove because will have dl matching errors since score('-','.')=1 which passes
                        if base_entity not in chain_entities:
                            chain_entities[base_entity]=[cat,str(elem)]#need to change so use list instead of tuple
                        else:
                            chain_entities[base_entity][1]+='|'+str(elem)

                    if 'and' in lst and 'bar' in lst:#de luca cucina and bar
                        partial=lst[0:lst.index('and')]
                        self.insert(partial,cat,elem)

                    for i in range(len(lst)):#& <=> and
                        if lst[i]=='&':
                            lst[i]='and'
                            self.insert(lst,cat,elem)
                        elif lst[i]=='and':
                            lst[i]='&'
                            self.insert(lst,cat,elem)

                    if ',' in lst:#hotel vitale, ...
                        partial=lst[0:lst.index(',')]
                        self.insert(partial,cat,elem)
                        for i in range(len(partial)):#& <=> and
                            if partial[i]=='&':
                                partial[i]='and'
                                self.insert(partial,cat,elem)
                            elif partial[i]=='and':
                                partial[i]='&'
                                self.insert(partial,cat,elem)

                    if len(lst[0])==2:#sw hotel <-> s.w. hotel
                        acron=lst.pop(0)#treated as acronym
                        lst.insert(0,'.')
                        lst.insert(0,acron[1])
                        lst.insert(0,'.')
                        lst.insert(0,acron[0])
                        self.insert(lst,cat,elem)
                        for i in range(len(lst)):#& <=> and
                            if lst[i]=='&':
                                lst[i]='and'
                                self.insert(lst,cat,elem)
                            elif lst[i]=='and':
                                lst[i]='&'
                                self.insert(lst,cat,elem)
                        
        for entity in chain_entities:
            entity_list=entity.split()
            entity_info=chain_entities[entity]
            if '|' not in entity_info[1]:
                continue
            self.insert(entity_list,entity_info[0],entity_info[1])
            for i in range(len(entity_list)):#& <=> and
                if entity_list[i]=='&':
                    entity_list[i]='and'
                    self.insert(entity_list,entity_info[0],entity_info[1])
                elif entity_list[i]=='and':
                    entity_list[i]='&'
                    self.insert(entity_list,entity_info[0],entity_info[1])

    def initialize_w_ref(self,dic):#add db_dic if-/>
        #extract ref knowledge from db_dic TBDDDDDDDDDD
        #start of initialization
        dig=False
        chain_entities={}#keeping track of chain restaurants' ids i.e. {'entity name':('cat','id1|id2|id3|...')}
        for cat in dic.keys():
            for elem in dic[cat]:
                record = dic[cat][elem]

                if ('name' in record and record['name'] is not None):
                    new_name=record['name'].lower().strip()#cleans up name
                    if new_name == cat:
                        print('exceptional entity---------------------')
                        continue
                    lst=[]#final list that is used to insert into bt
                    dlst=[]
                    alt_dlst=[]
                    no_punc_lst=[]
                    plst=Word_Tokenize(Clean_Text(new_name))
                    #p=re.compile(r"^(\w+)(\'\w+)$")

                    for i in range (len(plst)):
                        if plst[i].isnumeric():
                            dig=True
                            for alt_dig in plst[i]:
                                alt_dlst.append(simple_num2words(int(alt_dig)))

                            converted=num2words(plst[i])
                            if '-' in converted:
                                converted_lst=converted.split('-')
                                for digword in converted_lst:
                                    dlst.append(digword)
                            else:
                                converted_lst=converted.split()
                                for digword in converted_lst:
                                    dlst.append(digword)
                            lst.append(plst[i])
                            continue
                        else:
                            lst.append(plst[i])
                            dlst.append(plst[i])
                            alt_dlst.append(plst[i])
                    
                    for w in lst:
                        if elem.isalnum():
                            no_punc_lst.append(elem)
                    
                    self.restricted_insert(lst,cat,elem)
                    self.restricted_insert(no_punc_lst,cat,elem)

                    if dig:
                        self.restricted_insert(dlst,cat,elem)
                        self.restricted_insert(alt_dlst,cat,elem)

                    if '-' in lst:#chain rest: xxx - xxx
                        base_entity=' '.join(lst[0:lst.index('-')])
                        lst.remove('-')#we won't have these types of punc in logs. remove because will have dl matching errors since score('-','.')=1 which passes
                        self.restricted_insert(lst,cat,elem)
                        if base_entity not in chain_entities:
                            chain_entities[base_entity]=[cat,str(elem)]#need to change so use list instead of tuple
                        else:
                            chain_entities[base_entity][1]+='|'+str(elem)
                    
                    if 'and' in lst and 'bar' in lst:#de luca cucina and bar
                        partial=lst[0:lst.index('and')]
                        self.insert(partial,cat,elem)
                        
                    for i in range(len(lst)):#& <=> and
                        if lst[i]=='&':
                            lst[i]='and'
                            self.restricted_insert(lst,cat,elem)
                        elif lst[i]=='and':
                            lst[i]='&'
                            self.restricted_insert(lst,cat,elem)

                    if ',' in lst:#hotel vitale, ...
                        partial=lst[0:lst.index(',')]
                        self.restricted_insert(partial,cat,elem)
                        for i in range(len(partial)):#& <=> and
                            if partial[i]=='&':
                                partial[i]='and'
                                self.restricted_insert(partial,cat,elem)
                            elif partial[i]=='and':
                                partial[i]='&'
                                self.restricted_insert(partial,cat,elem)

                    if len(lst[0])==2:#sw hotel <-> s.w. hotel
                        acron=lst.pop(0)#treated as acronym
                        lst.insert(0,acron[1]+'.')
                        lst.insert(0,acron[0]+'.')
                        self.restricted_insert(lst,cat,elem)
                        for i in range(len(lst)):#& <=> and
                            if lst[i]=='&':
                                lst[i]='and'
                                self.restricted_insert(lst,cat,elem)
                            elif lst[i]=='and':
                                lst[i]='&'
                                self.restricted_insert(lst,cat,elem)
                        
        for entity in chain_entities:
            entity_list=entity.split()
            entity_info=chain_entities[entity]
            if '|' not in entity_info[1]:
                continue
            self.restricted_insert(entity_list,entity_info[0],entity_info[1])
            for i in range(len(entity_list)):#& <=> and
                if entity_list[i]=='&':
                    entity_list[i]='and'
                    self.restricted_insert(entity_list,entity_info[0],entity_info[1])
                elif entity_list[i]=='and':
                    entity_list[i]='&'
                    self.restricted_insert(entity_list,entity_info[0],entity_info[1])
    
    def sp_initialize(self,spdic):
        dig=False
        chain_entities={}
        #only for db.json in dstc10_track2_task1
        for cat in spdic.keys():
            for entry in spdic[cat]:
                if (entry['id'] is not None) and (entry['name'] is not None):
                    new_name=entry['name'].lower().strip()#cleans up name
                    if new_name == cat:
                        print('exceptional entity---------------------')
                        continue
                    lst=[]#final list that is used to insert into bt
                    dlst=[]
                    plst=Word_Tokenize(Clean_Text(new_name))#need to go through dig process below

                    for i in range (len(plst)):
                        if plst[i].isnumeric():
                            dig=True
                            converted=num2words(plst[i])
                            if '-' in converted:
                                converted_lst=converted.split('-')
                                for digword in converted_lst:
                                    dlst.append(digword)
                            else:
                                converted_lst=converted.split()
                                for digword in converted_lst:
                                    dlst.append(digword)
                            lst.append(plst[i])
                            continue
                        else:
                            dig=False
                            lst.append(plst[i])
                            dlst.append(plst[i])

                    self.insert(lst,cat,entry['id'])

                    if dig:
                        print(dlst)
                        self.insert(dlst,cat,entry['id'])

                    if '-' in lst:#chain rest: xxx - xxx
                        base_entity=' '.join(lst[0:lst.index('-')])
                        lst.remove('-')#we won't have these types of punc in logs. remove because will have dl matching errors since score('-','.')=1 which passes
                        if base_entity not in chain_entities:
                            chain_entities[base_entity]=[cat,str(entry['id'])]#need to change so use list instead of tuple
                        else:
                            chain_entities[base_entity][1]+='|'+str(entry['id'])

                    if 'and' in lst and 'bar' in lst:#de luca cucina and bar
                        partial=lst[0:lst.index('and')]
                        self.insert(partial,cat,entry['id'])

                    for i in range(len(lst)):#& <=> and
                        if lst[i]=='&':
                            lst[i]='and'
                            self.insert(lst,cat,entry['id'])
                        elif lst[i]=='and':
                            lst[i]='&'
                            self.insert(lst,cat,entry['id'])

                    if ',' in lst:#hotel vitale, ...
                        partial=lst[0:lst.index(',')]
                        self.insert(partial,cat,entry['id'])
                        for i in range(len(partial)):#& <=> and
                            if partial[i]=='&':
                                partial[i]='and'
                                self.insert(partial,cat,entry['id'])
                            elif partial[i]=='and':
                                partial[i]='&'
                                self.insert(partial,cat,entry['id'])

                    if len(lst[0])==2:#sw hotel <-> s.w. hotel
                        acron=lst.pop(0)#treated as acronym
                        lst.insert(0,'.')
                        lst.insert(0,acron[1])
                        lst.insert(0,'.')
                        lst.insert(0,acron[0])
                        self.insert(lst,cat,entry['id'])
                        for i in range(len(lst)):#& <=> and
                            if lst[i]=='&':
                                lst[i]='and'
                                self.insert(lst,cat,entry['id'])
                            elif lst[i]=='and':
                                lst[i]='&'
                                self.insert(lst,cat,entry['id'])
                        
        for entity in chain_entities:
            entity_list=entity.split()
            entity_info=chain_entities[entity]
            if '|' not in entity_info[1]:
                continue
            self.insert(entity_list,entity_info[0],entity_info[1])
            for i in range(len(entity_list)):#& <=> and
                if entity_list[i]=='&':
                    entity_list[i]='and'
                    self.insert(entity_list,entity_info[0],entity_info[1])
                elif entity_list[i]=='and':
                    entity_list[i]='&'
                    self.insert(entity_list,entity_info[0],entity_info[1])

    def initialize_multiwoz(self):
        dic_lst = ['',
                   '',
                   '',
                   '',
                   '',
                   '',
                   '',
                   
        ]
        for f in dic_lst:
            print('Starting ', f)
            db = open(f,'r')
            dic = json.load(db)
            db.close()
            dig=False
            chain_entities={}#keeping track of chain restaurants' ids i.e. {'entity name':('cat','id1|id2|id3|...')}
            for record in dic:            
                if ('name' in record and record['name'] is not None and 'type' in record and record['type'] is not None):
                    new_name=record['name'].lower().strip()#cleans up name
                    cat = record['type']
                    if 'id' in record and record['id'] is not None:
                        elem = record['id']
                    else:
                        elem = 'xxx'
                    if new_name == cat:
                        print('exceptional entity---------------------')
                        continue
                    lst=[]#final list that is used to insert into bt
                    dlst=[]
                    alt_dlst=[]
                    no_punc_lst=[]
                    plst=Word_Tokenize(Clean_Text(new_name))
                    #p=re.compile(r"^(\w+)(\'\w+)$")
    
                    for i in range (len(plst)):
                        if plst[i].isnumeric():
                            dig=True
                            for alt_dig in plst[i]:
                                alt_dlst.append(simple_num2words(int(alt_dig)))
    
                            converted=num2words(plst[i])
                            if '-' in converted:
                                converted_lst=converted.split('-')
                                for digword in converted_lst:
                                    dlst.append(digword)
                            else:
                                converted_lst=converted.split()
                                for digword in converted_lst:
                                    dlst.append(digword)
                            lst.append(plst[i])
                            continue
                        else:
                            lst.append(plst[i])
                            dlst.append(plst[i])
                            alt_dlst.append(plst[i])
                    
                    for w in lst:
                        if w.isalnum():
                            no_punc_lst.append(w)
                    
                    self.restricted_insert(lst,cat,elem)
                    self.restricted_insert(no_punc_lst,cat,elem)
    
                    if dig:
                        self.restricted_insert(dlst,cat,elem)
                        self.restricted_insert(alt_dlst,cat,elem)
    
                    if '-' in lst:#chain rest: xxx - xxx
                        base_entity=' '.join(lst[0:lst.index('-')])
                        lst.remove('-')#we won't have these types of punc in logs. remove because will have dl matching errors since score('-','.')=1 which passes
                        self.restricted_insert(lst,cat,elem)
                        if base_entity not in chain_entities:
                            chain_entities[base_entity]=[cat,str(elem)]#need to change so use list instead of tuple
                        else:
                            chain_entities[base_entity][1]+='|'+str(elem)
                    
                    if 'and' in lst and 'bar' in lst:#de luca cucina and bar
                        partial=lst[0:lst.index('and')]
                        self.insert(partial,cat,elem)
                        
                    for i in range(len(lst)):#& <=> and
                        if lst[i]=='&':
                            lst[i]='and'
                            self.restricted_insert(lst,cat,elem)
                        elif lst[i]=='and':
                            lst[i]='&'
                            self.restricted_insert(lst,cat,elem)
    
                    if ',' in lst:#hotel vitale, ...
                        partial=lst[0:lst.index(',')]
                        self.restricted_insert(partial,cat,elem)
                        for i in range(len(partial)):#& <=> and
                            if partial[i]=='&':
                                partial[i]='and'
                                self.restricted_insert(partial,cat,elem)
                            elif partial[i]=='and':
                                partial[i]='&'
                                self.restricted_insert(partial,cat,elem)
    
                    if len(lst[0])==2:#sw hotel <-> s.w. hotel
                        acron=lst.pop(0)#treated as acronym
                        lst.insert(0,acron[1]+'.')
                        lst.insert(0,acron[0]+'.')
                        self.restricted_insert(lst,cat,elem)
                        for i in range(len(lst)):#& <=> and
                            if lst[i]=='&':
                                lst[i]='and'
                                self.restricted_insert(lst,cat,elem)
                            elif lst[i]=='and':
                                lst[i]='&'
                                self.restricted_insert(lst,cat,elem)
                        
        for entity in chain_entities:
            entity_list=entity.split()
            entity_info=chain_entities[entity]
            if '|' not in entity_info[1]:
                continue
            self.restricted_insert(entity_list,entity_info[0],entity_info[1])
            for i in range(len(entity_list)):#& <=> and
                if entity_list[i]=='&':
                    entity_list[i]='and'
                    self.restricted_insert(entity_list,entity_info[0],entity_info[1])
                elif entity_list[i]=='and':
                    entity_list[i]='&'
                    self.restricted_insert(entity_list,entity_info[0],entity_info[1])
def main():
    kb=open('/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data_eval/knowledge.json','r')
    dic=json.load(kb)

    bt=BabyTrie()
    bt.initialize_w_ref(dic)
    kb.close()
    res=bt.isinTrie("ram's hotel")
    #print(res[0],res[1],res[2],sep='\n')
    print(res)

if __name__=='__main__':
    main()
