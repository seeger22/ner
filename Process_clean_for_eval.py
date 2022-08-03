import time
import json
import re
import argparse
from BabyTrie_DSTC10_v3 import BabyTrie
from extra_methods import convert_text2num#may have bugs such as for 'second one' = 3
from g2p_en import G2p
from simple_tokenize import Clean_Text
from simple_tokenize import Word_Tokenize#the words are tokenized the same way; can choose not to use this

def getphoneme(g2p,text):
    ptext=g2p(text)
    string='-'.join(ptext)
    res=string.replace('- -','_')
    return res

def gettemplate_wmap(bt,g2p,title):
    title = re.sub(r'\u2019', "'", title)
    title=Clean_Text(title).replace('\n',' ')
    nltk=' '.join(Word_Tokenize(title))

    word_lst,ind_dic=bt.isinTrie(title)
    nlst=Word_Tokenize(Clean_Text(title))
    new_sen=title.strip()#cleans up sentence
    
    en_dic={}
    title_phoneme=title
    for key in ind_dic:
        ind_lst=ind_dic[key]
        for pair in ind_lst:
            temp_str=''
            for index in range(pair[0][0],pair[0][1]+1):
                if not nlst[index][0].isalnum():
                    temp_str=temp_str[:-1]
                if nlst[index]=='-':
                    temp_str+=nlst[index]
                else:
                    temp_str+=nlst[index]+' '
            temp_str=temp_str[:-1]#getting rid of last space
            #temp_str_converted=convert_text2num(temp_str)#name entity to be in dig form
            phoneme_temp_str=getphoneme(g2p,temp_str)
            en_dic['<'+key+'-'+str(pair[1])+'>']=temp_str
            title_phoneme=title_phoneme.replace(temp_str,'<'+phoneme_temp_str+'>')
            title=title.replace(temp_str,'<'+key+'-'+str(pair[1])+'>')
    return [title,en_dic,title_phoneme,nltk]
  
def getkbtemplate(bt,g2p,title):
    title = re.sub(r'\u2019', "'", title)
    #Already has the cleaned/word_tokenized version
    title=title.replace('\n',' ')
    title_phoneme=title
    word_lst,ind_dic=bt.isinTrie(title)
    nlst=Word_Tokenize(Clean_Text(title))
    new_sen=title.strip()#cleans up sentence
    
    for key in ind_dic:
        ind_lst=ind_dic[key]
        for pair in ind_lst:
            temp_str=''
            for index in range(pair[0][0],pair[0][1]+1):
                if not nlst[index][0].isalnum():
                    temp_str=temp_str[:-1]
                temp_str+=nlst[index]+' '
            temp_str=temp_str[:-1]#getting rid of last space
            phoneme_temp_str=getphoneme(g2p,temp_str)
            title_phoneme=title.replace(temp_str,'<'+phoneme_temp_str+'>')
            title=title.replace(temp_str,'this '+key)

    insensitive_the_this=re.compile(re.escape('the this'),re.IGNORECASE)
    title=insensitive_the_this.sub('this',title)

    if title[0:4]=='this':
        title=title.replace('t','T',1)

    title=title.replace(' .','.')

    return (title,title_phoneme)

def run_dstc9_log(bt,data):
    #funciton works with: dstc9 logs, logs_eval, and dstc10 task1 + task2 logs.
    g2p=G2p()
    n=0
    ans_dic={}
    for dialogue in data:
        for section in dialogue:
            if section['text'] in ans_dic:
                info_lst=ans_dic[section['text']]
                section['template']=info_lst[0]
                section['id_map']=info_lst[1]
                section['phoneme_template']=info_lst[2]
                section['text_nltk']=info_lst[3]
                print('\t\t\tDUPLICATE')
            else:
                info_lst=gettemplate_wmap(bt,g2p,section['text'])
                section['template']=info_lst[0]
                section['id_map']=info_lst[1]
                section['phoneme_template']=info_lst[2]
                section['text_nltk']=info_lst[3]
                ans_dic[section['text']]=info_lst
                print('\t\t\tNEW')
                print(info_lst[0],info_lst[1],info_lst[2],info_lst[3],sep='\n')
            n+=1
            print('line/execution #',n,'--------------')
    return data

def run_dstc9_kb(bt,dic):
    #function works with: dstc9 kb, kb_eval, and dstc10 task2 kb. dstc10 task1 db has no doc entries (pure info)
    g2p=G2p()
    n=0
    for cat in dic:
        for num in dic[cat]:
            entity=dic[cat][num]['name']
            if not entity:#skip the taxi stuff
                continue
            entity_phoneme=getphoneme(g2p,entity)
            dic[cat][num]['phoneme_name']=entity_phoneme
            sen_dic=dic[cat][num]['docs']
            for entry in sen_dic:

                found_in_title=False
                found_in_body=False

                title=Clean_Text(sen_dic[entry]['title']).replace('\n',' ')
                title = re.sub(r'\u2019', "'", title)
                if entity=="ROSA'S BED AND BREAKFAST" and entry=='30':
                    print(title)
                    time.sleep(10)
                body=Clean_Text(sen_dic[entry]['body']).replace('\n',' ')
                body = re.sub(r'\u2019', "'", body)

                title_nltk=" ".join(Word_Tokenize(title))
                body_nltk=" ".join(Word_Tokenize(body))
                sen_dic[entry]['title_nltk']=title_nltk
                sen_dic[entry]['body_nltk']=body_nltk

                title_l=title.lower()
                if entity=="ROSA'S BED AND BREAKFAST" and entry=='30':
                    print(title_l)
                    time.sleep(10)
                body_l=body.lower()
                insensitive_entity = re.compile(re.escape(entity), re.IGNORECASE)
                
                if entity.lower() in title_l:
                    rtitle=insensitive_entity.sub('this '+cat,title)
                    ptitle_phoneme=insensitive_entity.sub('<'+entity_phoneme+'>',title)
                    if entity=="ROSA'S BED AND BREAKFAST" and entry=='30':
                        print(title)
                        print(rtitle)
                        time.sleep(10)
                    found_in_title=True
                if entity.lower() in body_l:
                    rbody=insensitive_entity.sub('this '+cat,body)
                    pbody_phoneme=insensitive_entity.sub('<'+entity_phoneme+'>',body)
                    found_in_body=True
                #secondary process: strings that has edit distance 2 (if len 4~5) or 3 (if len>8) will also be matched/replaced
                if not found_in_title:
                    rtitle,ptitle_phoneme=getkbtemplate(bt,g2p,title)
                    if rtitle!=title:
                        found_in_title=True
                if not found_in_body:
                    rbody,pbody_phoneme=getkbtemplate(bt,g2p,body)
                    if rbody!=body:
                        found_in_body=True
                
                subs_lst=['this location','your location','the location',
                          'your site','this site','the site',
                          'your restaurant','this restaurant','the restaurant',
                          'the property','this property','your property',
                          'your hotel','this hotel','the hotel',
                          'your facility','this facility','the facility',
                          'your bar','this bar','the bar',
                          'there?','here?','there.','here.']

                if not found_in_title:#still not found? replace/add in there for reference
                    new_title=title
                    for subs in subs_lst:#try to find stuff from list above to replace
                        insensitive_repl = re.compile(re.escape(subs), re.IGNORECASE)
                        if found_in_title==True:
                            break
                        if insensitive_repl.search(title)!=None:
                            if subs=='there?' or subs=='here?':
                                new_title=insensitive_repl.sub('at '+entity+'?',title)
                                rtitle=insensitive_repl.sub('at this '+cat+'?',title)
                                ptitle_phoneme=insensitive_repl.sub('at <'+entity_phoneme+'>?',title)
                            else:
                                new_title=insensitive_repl.sub(entity,title)
                                rtitle=insensitive_repl.sub('this '+cat,title)
                                ptitle_phoneme=insensitive_repl.sub('<'+entity_phoneme+'>',title)
                            found_in_title=True
                            new_title=new_title.replace('The this','This',1)
                            new_title=new_title.replace('the this','This',1)
                            if new_title[0:4]=='this':
                                new_title=new_title.replace('this','This',1)
                            sen_dic[entry]['title_mod']=new_title
                    if not found_in_title:#ADD as last resort
                        last=title[-1]
                        if not last.isalnum():#if last is a punc
                            new_title=title.replace(last,' at '+entity+last,1)
                            rtitle=title.replace(last,' at this '+cat+last,1)
                            ptitle_phoneme=title.replace(last,' at <'+entity_phoneme+'>'+last,1)
                        else:#if not default as a question
                            new_title=title+' at '+entity+'?'
                            rtitle=title+' at this '+cat+'?'
                            ptitle_phoneme=title+' at <'+entity_phoneme+'>?'
                        new_title=new_title.replace('The this','This',1)
                        new_title=new_title.replace('the this','This',1)
                        if new_title[0:4]=='this':
                            new_title=new_title.replace('this','This',1)
                        sen_dic[entry]['title_mod']=new_title
                    #print('title: '+rtitle,'title_mod: '+new_title,'title_phon: '+ptitle_phoneme,sep='\n')
                rtitle=rtitle.replace('The this','This',1)
                rtitle=rtitle.replace('the this','This',1)
                if rtitle[0:4]=='this':
                    rtitle=rtitle.replace('this','This',1)
                ptitle_phoneme=ptitle_phoneme.replace('The this','This',1)
                ptitle_phoneme=ptitle_phoneme.replace('the this','This',1)
                if ptitle_phoneme[0:4]=='this':
                    ptitle_phoneme=ptitle_phoneme.replace('this','This',1)
                
                sen_dic[entry]['title_template']=rtitle
                sen_dic[entry]['title_phoneme']=ptitle_phoneme#comment out right now
                if not found_in_body:
                    new_body=body
                    for subs in subs_lst:
                        insensitive_repl = re.compile(re.escape(subs), re.IGNORECASE)
                        if found_in_body==True:
                            break
                        if insensitive_repl.search(body)!=None:
                            if subs=='there.' or subs=='here.':
                                new_body=insensitive_repl.sub('at '+entity+'.',body)
                                rbody=insensitive_repl.sub('at this '+cat+'.',body)
                                pbody_phoneme=insensitive_repl.sub('at <'+entity_phoneme+'>.',body)
                            else:
                                new_body=insensitive_repl.sub(entity,body)
                                rbody=insensitive_repl.sub('this '+cat,body)
                                pbody_phoneme=insensitive_repl.sub('<'+entity_phoneme+'>',body)
                            found_in_body=True
                            new_body=new_body.replace('The this','This',1)
                            new_body=new_body.replace('the this','This',1)
                            if new_body[0:4]=='this':
                                new_body=new_body.replace('this','This',1)
                            sen_dic[entry]['body_mod']=new_body
                    if not found_in_body:#ADD as last resort
                        last=body[-1]
                        if not last.isalnum():#if last is a punc
                            new_body=body.replace(last,' at '+entity+last,1)
                            rbody=body.replace(last,' at this '+cat+last,1)
                            pbody_phoneme=body.replace(last,' at <'+entity_phoneme+'>'+last,1)
                        else:#if not default as full stop
                            new_body=body+' at '+entity+'.'
                            rbody=body+' at this '+cat+'.'
                            pbody_phoneme=body+' at <'+entity_phoneme+'>.'
                        new_body=new_body.replace('The this','This',1)
                        new_body=new_body.replace('the this','This',1)
                        if new_body[0:4]=='this':
                            new_body=new_body.replace('this','This',1)
                        sen_dic[entry]['body_mod']=new_body
                        
                rbody=rbody.replace('The this','This',1)
                rbody=rbody.replace('the this','This',1)
                if rbody[0:4]=='this':
                    rbody=rbody.replace('this','This',1)
                pbody_phoneme=pbody_phoneme.replace('The this','This',1)
                pbody_phoneme=pbody_phoneme.replace('the this','This',1)
                if pbody_phoneme[0:4]=='this':
                    pbody_phoneme=pbody_phoneme.replace('this','This',1)
                sen_dic[entry]['body_template']=rbody
                sen_dic[entry]['body_phoneme']=pbody_phoneme
                n+=1
                print('line/execution #',n,'--------------')
    return dic

def run_labels(bt,lb):
    g2p=G2p()
    n=0
    ans_dic={}
    for entry in lb:
        if entry['target']==True:
            text=entry['response']
            if text in ans_dic:
                info_lst=ans_dic[text]
                entry['response_template']=info_lst[0]
                entry['response_id_map']=info_lst[1]
                entry['response_phoneme']=info_lst[2]
                entry['response_nltk']=info_lst[3]
                print('\t\t\tDUPLICATE')
                continue
            info_lst=gettemplate_wmap(bt,g2p,text)
            ans_dic[text]=info_lst
            entry['response_template']=info_lst[0]
            entry['response_id_map']=info_lst[1]
            entry['response_phoneme']=info_lst[2]
            entry['response_nltk']=info_lst[3]
            print('\t\t\tNEW')
            print(info_lst[0],info_lst[1],info_lst[2],info_lst[3],sep='\n')
            n+=1
            print('line/execution #',n,'--------------')
    return lb


def main():
    '''
    kb=open('knowledge_mod.json','r')
    dic=json.load(kb)

    bt=BabyTrie()
    bt.initialize(dic)
    kb.close()
    title='Alpha-Milton Guest House'
    res=gettemplate_wmap(bt,title)
    print(res[0],res[1],res[2],sep='\n')
    #print(res)
    '''
    parser=argparse.ArgumentParser(description='DSTC10 Data Preprocessing (Summer 2021) For Wilson. Error Correction with clean text')
    parser.add_argument("--testmode",type=bool,default=False,help='set True if testing')
    parser.add_argument("--quick_selection",type=float,default=0,help='*0 to skip*  1.1: dstc9_log; 1.2: dstc9_kb; 2.1: dstc9_log_eval; 2.2: dstc9_kb_eval; 3:dstc10_task1 logs; 4:dstc10_task2 logs')
    parser.add_argument("--log_file",type=str,default='logs.json',help="input log file to be templated")
    parser.add_argument("--knowledge_file",type=str,default='knowledge.json',help="input knowledge file")
    parser.add_argument("--template_sel",type=float,default=1.2,help="select 1.1: template logs (not dstc10 task1); 1.2: template kb; 2: template dstc10 task1 logs")
    parser.add_argument("--output_file",type=str,default='output.txt',help="output templated file")
    
    args = parser.parse_args()

    if args.quick_selection==7:
        g2p=G2p()
        key_dic=open('keyword.txt','r')
        ans_dic={}
        out=open('phoneme_keyword.json','w')
        n=0
        for word in key_dic.read().split():
            if word in ans_dic:
                print('\t\t\tDUPLICATE')
                continue
            phon_word=getphoneme(g2p,word)
            ans_dic[word]=phon_word
            print('\t\t\tNEW')
            print(word,' ---> ',phon_word)
            n+=1
            print('line/execution #',n,'--------------')
        print('Dumping......')
        json.dump(ans_dic,out,indent=4)
        print('Done.')

    if args.quick_selection==6:
        g2p=G2p()
        print('Collecting Phoneme dictionary......')
        #FILE NEEDS TO BE CHANGED IF RUNNING ON HPC: CHANGE QUICK SELECTION?
        logs=['logs_mod.json',
              '/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data/val/logs.json',
              '/content/drive/MyDrive/Research/ner/alexa-with-dstc10-track2-dataset/task2/data/val/logs.json',
              '/content/drive/MyDrive/Research/ner/alexa-with-dstc10-track2-dataset/task1/data/val/logs.json'
              ]
        kb='/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data_eval/knowledge.json'
        out=open('phoneme_dic.json','w')
        phoneme_dic={}
        for i in range(len(logs)):
            n=0
            print('Processing log #',i,'......')
            log=open(logs[i],'r')
            data=json.load(log)
            for dialogue in data:
                for section in dialogue:
                    ws_lst=section['text'].split()
                    for word in ws_lst:
                        if word in phoneme_dic:
                            print('\t\t\tDUPLICATE')
                            continue
                        phon_word=getphoneme(g2p,word)
                        phoneme_dic[word]=phon_word
                        print('\t\t\tNEW')
                        print(word,' ---> ',phon_word)
                    n+=1
                    print('line/execution #',n,'--------------')
            log.close()
        n=0
        print('Processing kb......')
        knowledge=open(kb,'r')
        dic=json.load(knowledge)
        for cat in dic:
            for num in dic[cat]:
                entity=dic[cat][num]['name']
                sen_dic=dic[cat][num]['docs']
                if not entity:#skip the taxi stuff
                    continue
                enti_lst=entity.split()
                for word in enti_lst:
                    if word in phoneme_dic:
                        print('\t\t\tDUPLICATE')
                        continue
                    phon_word=getphoneme(g2p,word)
                    phoneme_dic[word]=phon_word
                    print('\t\t\tNEW')
                    print(word,' ---> ',phon_word)
                for entry in sen_dic:
                    title=sen_dic[entry]['title']
                    body=sen_dic[entry]['body']
                    title_lst=title.split()
                    body_lst=body.split()
                    for word in title_lst:
                        if word in phoneme_dic:
                            print('\t\t\tDUPLICATE')
                            continue
                        phon_word=getphoneme(g2p,word)
                        phoneme_dic[word]=phon_word
                        print('\t\t\tNEW')
                        print(word,' ---> ',phon_word)
                    for word in body_lst:
                        if word in phoneme_dic:
                            print('\t\t\tDUPLICATE')
                            continue
                        phon_word=getphoneme(g2p,word)
                        phoneme_dic[word]=phon_word
                        print('\t\t\tNEW')
                        print(word,' ---> ',phon_word)
                    n+=1
                    print('line/execution #',n,'--------------')
        knowledge.close()
        print('Dumping......')
        json.dump(phoneme_dic,out,indent=4)
        out.close()
        print('Done.')

    if args.quick_selection==5:#~1hr 30 min
        print('Running labels batch......')
        labels=['/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data/train/labels.json',
                '/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data/val/labels.json',
                '/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data_eval/test/labels.json',
                '/content/drive/MyDrive/Research/ner/alexa-with-dstc10-track2-dataset/task2/data/val/labels.json'
                
        ]
        kbs=['knowledge_mod.json',
             '/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data_eval/knowledge.json'
        ]
        outs=['DSTC9_task1_train_labels_phon_templates.json',
              'DSTC9_task1_val_labels_phon_templates.json',
              'DSTC9_task1_eval_labels_phon_templates.json',
              'DSTC10_track2_task2_labels_phon_templates.json'
        ]
        for i in range(len(labels)):
            out=open(outs[i],'w')
            label=open(labels[i],'r')
            lb=json.load(label)

            bt=BabyTrie()#setting up bt based on knowledge base
            if i<=1:
                kb=open(kbs[0],'r')
                dic=json.load(kb)
                bt.initialize(dic)
                print('Trie successfully initialized.')
            else:
                kb=open(kbs[1],'r')
                dic=json.load(kb)
                bt.initialize_w_ref(dic)
                print('Ref_Trie successfully initialized.')
            label.close()
            kb.close()
            new_data=run_labels(bt,lb)

            print('dumping...')
            json.dump(new_data,out,indent=4)
            out.close()
            print('Done.')

    elif args.quick_selection==1.1:
        out=open('DSTC9_task1_train_log_phon_templates.json','w')
        logs=open('logs_mod.json','r')
        data=json.load(logs)
        kb=open('knowledge_mod.json','r')
        dic=json.load(kb)

        bt=BabyTrie()#setting up bt based on knowledge base
        bt.initialize(dic)
        print('Trie successfully initialized.')
        logs.close()
        kb.close()
        new_data=run_dstc9_log(bt,data)

        print('dumping...')
        json.dump(new_data,out,indent=4)
        out.close()
        print('Done.')
    elif args.quick_selection==1.3:# 101,649 lines
        out=open('DSTC9_task1_val_log_phon_templates.json','w')
        logs=open('/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data/val/logs.json','r')
        data=json.load(logs)
        kb=open('knowledge_mod.json','r')
        dic=json.load(kb)

        bt=BabyTrie()#setting up bt based on knowledge base
        bt.initialize(dic)
        print('Trie successfully initialized.')
        logs.close()
        kb.close()
        new_data=run_dstc9_log(bt,data)

        print('dumping...')
        json.dump(new_data,out,indent=4)
        out.close()
        print('Done.')
    elif args.quick_selection==1.2:
        out=open('DSTC9_task1_kb_phon_templates.json','w')
        kb=open('knowledge_mod.json','r')
        dic=json.load(kb)

        bt=BabyTrie()#setting up bt based on knowledge base
        bt.initialize(dic)
        print('Trie successfully initialized.')
        kb.close()
        new_data=run_dstc9_kb(bt,dic)

        print('dumping...')
        json.dump(new_data,out,indent=4)
        out.close()
        print('Done.')
    elif args.quick_selection==2.1:
        out=open('DSTC10_task1_log_eval_phon_templates.json','w')
        logs=open('/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data_eval/test/logs.json','r')
        data=json.load(logs)
        kb=open('/content/drive/MyDrive/Research/ner/alexa-with-dstc10-track2-dataset/task2/data/knowledge.json','r')
        dic=json.load(kb)

        bt=BabyTrie()#setting up bt based on knowledge base
        bt.initialize_w_ref(dic)
        print('Trie successfully initialized.')
        logs.close()
        kb.close()
        new_data=run_dstc9_log(bt,data)

        print('dumping...')
        json.dump(new_data,out,indent=4)
        out.close()
        print('Done.')
    elif args.quick_selection==2.2:
        out=open('DSTC10_task2_kb_eval_phon_templates.json','w')
        kb=open('/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data_eval/knowledge.json','r')
        dic=json.load(kb)

        bt=BabyTrie()#setting up bt based on knowledge base
        bt.initialize_w_ref(dic)
        print('Trie successfully initialized.')
        kb.close()
        new_data=run_dstc9_kb(bt,dic)

        print('dumping...')
        json.dump(new_data,out,indent=4)
        out.close()
        print('Done.')
    elif args.quick_selection==3:
        out=open('DSTC10_task1_log_phon_templates.json','w')
        logs=open('/content/drive/MyDrive/Research/ner/alexa-with-dstc10-track2-dataset/task1/data/val/logs.json','r')
        data=json.load(logs)
        kb=open('/content/drive/MyDrive/Research/ner/alexa-with-dstc10-track2-dataset/task1/data/db.json','r')
        dic=json.load(kb)

        bt=BabyTrie()#setting up bt based on knowledge base
        bt.sp_initialize(dic)
        print('Special Trie successfully initialized.')
        logs.close()
        kb.close()
        new_data=run_dstc9_log(bt,data)

        print('dumping...')
        json.dump(new_data,out,indent=4)
        out.close()
        print('Done.')
    elif args.quick_selection==4:
        out=open('DSTC10_task2_log_eval_phon_templates.json','w')
        logs=open('/content/drive/MyDrive/Research/ner/alexa-with-dstc10-track2-dataset/task2/data/val/logs.json','r')
        data=json.load(logs)
        kb=open('/content/drive/MyDrive/Research/ner/alexa-with-dstc10-track2-dataset/task2/data/knowledge.json','r')
        dic=json.load(kb)

        bt=BabyTrie()#setting up bt based on knowledge base
        bt.initialize_w_ref(dic)
        print('Trie successfully initialized.')
        logs.close()
        kb.close()
        new_data=run_dstc9_log(bt,data)

        print('dumping...')
        json.dump(new_data,out,indent=4)
        out.close()
        print('Done.')

if __name__=='__main__':
    main()