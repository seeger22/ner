import random
import json
import re
import pickle
import time

def postprocess_text(query):
    #assumes sen to be delexicalized
    #remove from delexicalized data the likes of 'at this hotel'
    #only concerned about intent, delete most of the slot, domain references
    #will remove 'at this time'
    delete_list=[r" at this \w+",r" at the \w+",r" to the \w+",r" to this \w+",r" on this \w+",r" at your \w+",r" to your \w+",r" on your \w+",r" on the \w+"]
    #[r" on the \w+"]
    #figure out how to remove things like on this restaurant's menu?
    repl_list=[r"this \w+",r"This \w+"]

    for elem in delete_list:
        query = re.sub(elem, "", query)
    for elem in repl_list:
        query = re.sub(elem, "it", query)
        if query[0:2]=='it':#capitalize
            query=query.replace('it','It',1)
    #query = re.sub(r"This restaurant restaurant", "It", query)
    #query = re.sub(r"at this \w+", "", query)
    #query = re.sub(r"at the \w+", "", query)
    #query = re.sub(r"This \w+", "It ", query)

    return query

def special_mod(title,body):
    title_ex=title
    body_ex=body
    title=postprocess_text(title)
    body=postprocess_text(body)
    delete_list=[" onboard"," on board"," at any train station"," for all the trains"," for a delayed or cancelled train", r" in your \w+",r" onto the \w+", r" on the \w+",r" at the \w+",
                 r" in the \w+",r" for the \w+",r" to the \w+", " to get"," station"]
    for elem in delete_list:
        title_ex=re.sub(elem,"",title_ex)
        body_ex=re.sub(elem,"",body_ex)
    title_ex=title_ex.replace("Are the trains","Are they")
    body_ex=body_ex.replace("Are the trains","Are they")
    title_ex=title_ex.replace("all the trains","they are")
    body_ex=body_ex.replace("all the trains","they are")
    print(title_ex,body_ex,sep='\n')
    return title_ex,body_ex


def modify_kb():
    kb=open('/content/drive/MyDrive/Research/ner/DSTC9_task1_kb_eval_phon_templates.json','r')
    dic=json.load(kb)
    kb.close()
    new=open('kb_eval_ex.json','w')
    n=0
    for cat in dic:
        for elem in dic[cat]:
            if dic[cat][elem]['name'] is None:#train or taxi
                for entry in dic[cat][elem]['docs']:
                    curr=dic[cat][elem]['docs'][entry]
                    #print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    title_ex,body_ex=special_mod(curr['title'],curr['body'])
                    curr['title_ex']=title_ex
                    curr['body_ex']=body_ex
                continue
            for entry in dic[cat][elem]['docs']:
                curr=dic[cat][elem]['docs'][entry]
                title=postprocess_text(curr['title_template'])
                body=postprocess_text(curr['body_template'])
                #print(title)
                #print(body)
                curr['title_ex']=title
                curr['body_ex']=body
                n+=1
                print('line #',n,'--------')
    json.dump(dic,new,indent=4)
    print('Done.')

def get_cluster_map():
    res={}
    with open('kb_doc_clusters.pkl','rb') as F:
        pickle_obj1=pickle.load(F)
    with open('kb_doc_clusters2.pkl','rb') as F:
        pickle_obj2=pickle.load(F)
    lst1=[elem for elem in pickle_obj1 if len(elem)>1]#title matches
    lst2=[elem for elem in pickle_obj2 if len(elem)>1]#body matches

    for i in range(len(lst1)):
        res[i]=lst1[i]
    for j in range(len(lst2)):
        res[j]=lst2[j]
    return res
    

def more_neg(dic,cl_map,out,hm):
    n=0#example of negatives formed, 219918
    for cat in dic:
        for elem in dic[cat]:
            entity=dic[cat][elem]['name']
            doc_lst=dic[cat][elem]['docs']
            for entry in doc_lst:
                doc_id='_'.join([cat,elem,entry])
                curr=doc_lst[entry]
                for match in doc_lst:
                    mlst=[]
                    match_id='_'.join([cat,elem,match])
                    if match!=entry:
                        nv_flag=False#not valid flag
                        for cluster_id in cl_map:
                            if doc_id in cl_map[cluster_id]:
                                if match_id in cl_map[cluster_id]:
                                    nv_flag=True
                        if not nv_flag:
                            candidate={}
                            candidate['title']=doc_lst[entry]['title_ex']
                            candidate['body']=doc_lst[match]['body_ex']
                            candidate['label']='false'
                            pair=(candidate['title'],candidate['body'])
                            if pair not in hm:
                                print('execution #',n)
                                print(pair)
                                out.append(candidate)
                                hm[pair]=n
                                n-=1

                        


def find_comb(tlst,blst):
    rlst=[]
    for title in tlst:
        for i in range(len(blst)):
            pair=(title,blst[i])
            rlst.append(pair)#can have dupes, treated later with hm
    return rlst

def more_positive_ex(lst,typ):
    kb=open('kb_eval_ex.json','r')
    dic=json.load(kb)
    kb.close()

    ex_lst=[]
    tlst=[]#title list
    blst=[]#body list
    for elem in lst:
        cat,num,doc_id=elem.split('_')
        title=dic[cat][num]['docs'][doc_id]['title_ex']
        body=dic[cat][num]['docs'][doc_id]['body_ex']
        tlst.append(title)
        blst.append(body)
        #get every possible title/body out
    if typ==1:
        comb=find_comb(tlst,blst)
    elif typ==2:
        comb=find_comb(blst,tlst)
    for elem in comb:#dupes not checked here
        candidate={}
        if typ==1:
            candidate['title']=elem[0]
            candidate['body']=elem[1]
        else:
            candidate['title']=elem[1]
            candidate['body']=elem[0]
        candidate['label']='true'
        
        ex_lst.append(candidate)
        continue
    return ex_lst

def generate_from_pkl(hm,res):
    n=0#number of matched positive examples, 305016
    with open('kb_doc_clusters.pkl','rb') as F:
        pickle_obj1=pickle.load(F)
    with open('kb_doc_clusters2.pkl','rb') as F:
        pickle_obj2=pickle.load(F)
    lst1=[elem for elem in pickle_obj1 if len(elem)>1]#title matches
    lst2=[elem for elem in pickle_obj2 if len(elem)>1]#body matches
    for pairs in lst1:
        examples=more_positive_ex(pairs,1)
        for ex in examples:
            pair=(ex['title'],ex['body'])
            if pair not in hm:
                print(pair[0])
                print(pair[1])
                hm[pair]=str(n)
                n+=1
                print('execution #',n,'----------')
                res.append(ex)
    for pairs in lst2:
        examples=more_positive_ex(pairs,2)
        for ex in examples:
            pair=(ex['title'],ex['body'])
            if pair not in hm:
                print(pair[0])
                print(pair[1])
                hm[pair]=str(n)
                n+=1
                print('execution #',n,'----------')
                res.append(ex)
    return res,hm


def generate_from_kb():
    kb=open('kb_eval_ex.json','r')
    res=[]
    hm={}
    dic=json.load(kb)
    kb.close()
    n=0#total number of generic positive examples, 12008 (10483??)
    for category in dic:
        for number in dic[category]:
            entity_name=dic[category][number]['name']
            for entry in dic[category][number]['docs']:
                curr=(entry,dic[category][number]['docs'][entry])
                pair=(curr[1]['title_ex'],curr[1]['body_ex'])
                candidate={}
                candidate['title']=curr[1]['title_ex']
                candidate['body']=curr[1]['body_ex']
                candidate['label']='true'
                if pair not in hm:
                    hm[pair]=str(n)
                    res.append(candidate)
                    n+=1
                    print('execution #',n)
    print('Done.')
    return hm,res

def count_pairs(filepath):
    kb=open(filepath,'r')
    dic=json.load(kb)
    kb.close()
    n=0
    for category in dic:
        for number in dic[category]:
            if dic[category][number]['name'] is None:
                continue
            for entry in dic[category][number]['docs']:
                n+=1
    print(n)

def main():
    #print(postprocess_text("Live music is not being offered at this time at this train station."))
    modify_kb()
    '''
    kb=open('kb_eval_ex.json','r')
    dic=json.load(kb)
    kb.close()

    examples=open('classifier_examples.json','w')

    print('Generic Positives ------------------------------------------')
    map,lst=generate_from_kb()
    time.sleep(10)
    print('More positives ------------------------------------------')
    lst,map=generate_from_pkl(map,lst)
    time.sleep(10)
    print('Negatives ------------------------------------------')
    cl_map=get_cluster_map()
    more_neg(dic,cl_map,lst,map)
    random.shuffle(lst)
    json.dump(lst,examples,indent=4)
    examples.close()
    '''
if __name__=='__main__':
    main()