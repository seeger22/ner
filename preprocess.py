import json
import re
import argparse
from BabyTrie import BabyTrie
from argparse import Namespace

def get_bt(dic):
    '''
    Given a dictionary with categories of entities in the form:
    {'some category':{'0':{'name':'some name'},'1':{'name':'some other name'},...},'some other category':{'0':...},...}
    Return a BabyTrie that contains all entities and the leaf nodes contianing a list of their corresponding categories
    
    Note: A large portion of this code under the if statement is cleaning up the list of words within the name phrase
    -------------------------------------------------------------------------------------------------------------------
    Example:
    dic={'restaurant':{'0':{'name':'Jade Garden'}}}
    bt=get_bt(dic)#the name 'jade' and 'garden' are created as nodes and inserted into the BabyTrie
    
    '''
    bt=BabyTrie()
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
                bt.insert(lst,cat)
                for i in range(len(lst)):#& <=> and
                    if lst[i]=='&':
                        lst[i]='and'
                        bt.insert(lst,cat)
                    elif lst[i]=='and':
                        lst[i]='&'
                        bt.insert(lst,cat)
    return bt

def extraction_of_log1(lst):#in this case our log1 file (for train.txt) is a list of dictionaries
    res={}
    id=0
    for i in range(0,len(lst)):
        for elem in lst[i]:
            if elem['text'] not in res:
                res[elem['text']]=id
                id+=1
    return res

def extraction_of_log2(dic):
    res={}
    id=0
    for cat in dic.keys():
        for elem in dic[cat]:
            for dialogue_num in dic[cat][elem]['docs']:
                num1,num2=1,2
                if dic[cat][elem]['docs'][dialogue_num]['title'] not in res:
                    res[dic[cat][elem]['docs'][dialogue_num]['title']]=(id,num1)
                if dic[cat][elem]['docs'][dialogue_num]['body'] not in res:
                    res[dic[cat][elem]['docs'][dialogue_num]['body']]=(id,num2)
    return res

def printres(ofstream,res):
    '''
    Given a result tuple that is generated from the isinTrie method in the class of BabyTrie,
    Outputs the result in two columns containing labels in a file (tab in between)
    Note: the labeling of 'B_cat','I_cat', and 'O' is used.
    B_cat = begining of an entity of a category
    I_cat = intermediate (in the middle) of an entity of a category
    O = not an entity
    ----------------------------------------------------------------------------------------
    Example: (same output from isinTrie example)
    res=(['i','went','to','jade','garden','last','night','.'], {'restaurant':(3,4)})
                        lst                                            dic
    printres(res)

    Output:
    i       O
    went    O
    to      O
    jade    B-restaurant
    garden  I-restaurant
    last    O
    night   O
    .       O
    '''
    lst=res[0]
    dic=res[1]
    sen_label=[[word,'O'] for word in lst]
    for cat in dic.keys():
        for item in dic[cat]:
            start,end=item[0],item[1]
            first=True
            for i in range(start,end+1):
                if (sen_label[i][-1]!='O'):
                    if first:
                        record='|B-'+cat
                        first=False
                    else:
                        record='|I-'+cat
                    sen_label[i][-1]+=record
                else:
                    if first:
                        sen_label[i][-1]='B-'+cat
                        first=False
                    else:
                        sen_label[i][-1]='I-'+cat
    for elem in sen_label:
        ofstream.write('{}\t{}\n'.format(elem[0],elem[1]))
    ofstream.write('\n')

def printres_ne(ofstream,res):
    '''
    
    '''
    lst=res[0]
    dic=res[1]
    sen_label=[[word,'O'] for word in lst]
    if len(dic)==0:#if no entity in dic, do not output (testing)
        return
    for cat in dic.keys():
        for item in dic[cat]:
            start,end=item[0],item[1]
            first=True
            for i in range(start,end+1):
                if (sen_label[i][-1]!='O'):
                    if first:
                        record='|B-'+cat
                        first=False
                    else:
                        record='|I-'+cat
                    sen_label[i][-1]+=record
                else:
                    if first:
                        sen_label[i][-1]='B-'+cat
                        first=False
                    else:
                        sen_label[i][-1]='I-'+cat
    for elem in sen_label:
        ofstream.write('{}\t{}\n'.format(elem[0],elem[1]))
    ofstream.write('\n')

def printres_o(ofstream,res):
    '''
    
    '''
    lst=res[0]
    dic=res[1]
    sen_label=[[word,'O'] for word in lst]
    if len(dic)!=0:#if entity in dic, do not output (testing)
        return
    if 'attraction' not in dic:
        return
    for cat in dic.keys():
        for item in dic[cat]:
            start,end=item[0],item[1]
            first=True
            for i in range(start,end+1):
                if (sen_label[i][-1]!='O'):
                    if first:
                        record='|B-'+cat
                        first=False
                    else:
                        record='|I-'+cat
                    sen_label[i][-1]+=record
                else:
                    if first:
                        sen_label[i][-1]='B-'+cat
                        first=False
                    else:
                        sen_label[i][-1]='I-'+cat
    for elem in sen_label:
        ofstream.write('{}\t{}\n'.format(elem[0],elem[1]))
    ofstream.write('\n')

def main():

    parser=argparse.ArgumentParser(description='NER preprocess dataset')
    parser.add_argument("--log_file",type=str,default='logs.json',help="input log file in json")
    parser.add_argument("--knowledge_file",type=str,default='knowledge.json',help="input knowledge file in json")
    parser.add_argument("--output_file",type=str,default='output.txt',help="output file for NER training")
    parser.add_argument("--extract_lognum",type=int,default=1,help="1 for log (default), 2 for log included in knowledge base")
    parser.add_argument("--printres_type",type=int,default=1,help="1 for printres (default), 2 for printres_ne (only named entity sentences, 3 for printres_o (only non-named entities")
    args = parser.parse_args()
    
    #opens files first to load
    logs1=open(args.log_file,'r')
    data1=json.load(logs1)
    k=open(args.knowledge_file,'r')
    dic=json.load(k)
    

    bt=get_bt(dic)#setting up bt based on knowledge base
    if args.extract_lognum==1:
        dset=extraction_of_log1(data1)#extract logs1
    elif args.extract_lognum==2:
        dset=extraction_of_log2(dic)#extract additional data from knowledge base
    
    outFile=open(args.output_file,'w')
    for senkey in dset:#write results of log to file
        res=bt.isinTrie(senkey)
        if args.printres_type==1:
            printres(outFile,res)
        elif args.printres_type==2:
            printres_ne(outFile,res)
        elif args.printres_type==3:    
            printres_o(outFile,res)

    logs1.close()
    k.close()
    outFile.close()
    
if __name__ == "__main__":
    main()