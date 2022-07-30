#NOTE: lines in logs.json/logs_mod.json = 768,500
#NOTE: lines in logs_eval.json/logs_mod.json = 36,091
import json
import re
import argparse
from BabyTrie_DSTC10_v2_test import BabyTrie
from extra_methods import convert_text2num#may have bugs such as for 'second one' = 3
from g2p_en import G2p

def getphoneme(text):
    g2p=G2p()
    ptext=g2p(text)
    string='-'.join(ptext)
    res=string.replace('- -',' ')
    return res

def gettemplate_wmap(bt,title):
    #title=convert_text2num(title).strip()
    word_lst,ind_dic=bt.isinTrie(title)
    nlst=[]
    new_sen=title.strip()#cleans up sentence
    plst=re.findall(r"[\w']+|[.,!?;]", new_sen)#premature list used for clean-up
    p=re.compile(r"^(\w+)(\'\w+)$")
    for i in range (len(plst)):
        if p.match(plst[i]):
            new_word1,new_word2=p.match(plst[i]).group(1),p.match(plst[i]).group(2)
            nlst.append(new_word1)
            nlst.append(new_word2)
        else:
            nlst.append(plst[i])
    en_dic={}
    for key in ind_dic:
        ind_lst=ind_dic[key]
        for pair in ind_lst:
            temp_str=''
            for index in range(pair[0][0],pair[0][1]+1):
                if not nlst[index][0].isalnum():
                    temp_str=temp_str[:-1]
                temp_str+=nlst[index]+' '
            temp_str=temp_str[:-1]#getting rid of last space
            en_dic['<'+key+'-'+str(pair[1])+'>']=temp_str
            title=title.replace(temp_str,'<'+key+'-'+str(pair[1])+'>')
    return (title,en_dic)
  
def getkbtemplate(bt,title):
    word_lst,ind_dic=bt.isinTrie(title)
    nlst=[]
    new_sen=title.strip()#cleans up sentence
    plst=re.findall(r"[\w']+|[.,!?;]", new_sen)#premature list used for clean-up
    p=re.compile(r"^(\w+)(\'\w+)$")
    for i in range (len(plst)):
        if p.match(plst[i]):
            new_word1,new_word2=p.match(plst[i]).group(1),p.match(plst[i]).group(2)
            nlst.append(new_word1)
            nlst.append(new_word2)
        else:
            nlst.append(plst[i])
    for key in ind_dic:
        ind_lst=ind_dic[key]
        for pair in ind_lst:
            temp_str=''
            for index in range(pair[0][0],pair[0][1]+1):
                if not nlst[index][0].isalnum():
                    temp_str=temp_str[:-1]
                temp_str+=nlst[index]+' '
            temp_str=temp_str[:-1]#getting rid of last space
            title=title.replace(temp_str,'this '+key)

    insensitive_the_this=re.compile(re.escape('the this'),re.IGNORECASE)
    title=insensitive_the_this.sub('this',title)

    if title[0:4]=='this':
        title=title.replace('t','T',1)

    title=title.replace(' .','.')

    return (title)

def run_dstc9_log(bt,data):
    #funciton works with: dstc9 logs, logs_eval, and dstc10 task1 + task2 logs.
    n=0
    for dialogue in data:
        for section in dialogue:
            phoneme=getphoneme(section['text'])
            template,map=gettemplate_wmap(bt,section['text'])
            section['template']=template
            section['id_map']=map
            section['phoneme']=phoneme
            n+=1
            print('line/execution #',n)
    return data

def run_dstc9_kb(bt,dic):
    #function works with: dstc9 kb, kb_eval, and dstc10 task2 kb. dstc10 task1 db has no doc entries (pure info)
    n=0
    for cat in dic:
        for num in dic[cat]:
            entity=dic[cat][num]['name']
            if not entity:#skip the taxi stuff
                continue
            sen_dic=dic[cat][num]['docs']
            for entry in sen_dic:

                found_in_title=False
                found_in_body=False

                title=sen_dic[entry]['title']
                title_phoneme=getphoneme(title)
                body=sen_dic[entry]['body']
                body_phoneme=getphoneme(body)
                title_l=title.lower()
                body_l=body.lower()
                insensitive_entity = re.compile(re.escape(entity), re.IGNORECASE)
                
                if entity.lower() in title_l:
                    ptitle=insensitive_entity.sub('this '+cat,title)
                    found_in_title=True
                if entity.lower() in body_l:
                    pbody=insensitive_entity.sub('this '+cat,body)
                    found_in_body=True
                #secondary process: strings that has edit distance 2 (if len 4~5) or 3 (if len>8) will also be matched/replaced
                if not found_in_title:
                    ptitle=getkbtemplate(bt,title)
                if not found_in_body:
                    pbody=getkbtemplate(bt,body)
                
                rtitle=ptitle
                rbody=pbody
                sen_dic[entry]['title_template']=rtitle
                sen_dic[entry]['title_phoneme']=title_phoneme
                sen_dic[entry]['body_template']=rbody
                sen_dic[entry]['body_phoneme']=body_phoneme
                print('line: ',n)
                n+=1
    return dic

def run_labels(bt,lb):
    g2p=G2p()
    n=0
    for entry in lb:
        if entry['target']==True:
            text=entry['response']
            phoneme=getphoneme(text)
            template,map=gettemplate_wmap(bt,text)
            entry['response_template']=template
            entry['response_id_map']=map
            entry['response_phoneme']=phoneme
            n+=1
            print('line/execution #',n)
    return lb


def main():
    '''
    kb=open('knowledge_mod.json','r')
    dic=json.load(kb)

    bt=BabyTrie()
    bt.initialize(dic)
    kb.close()
    title='Does the Worth House offer a free breakfast?'
    res=getkbtemplate(bt,title)
    #print(res[0],res[1],res[2],sep='\n')
    print(res)
    '''
    parser=argparse.ArgumentParser(description='DSTC10 Data Preprocessing (Summer 2021)')
    parser.add_argument("--testmode",type=bool,default=False,help='set True if testing')
    parser.add_argument("--quick_selection",type=float,default=0,help='*0 to skip*  1.1: dstc9_log; 1.2: dstc9_kb; 2.1: dstc9_log_eval; 2.2: dstc9_kb_eval; 3:dstc10_task1 logs; 4:dstc10_task2 logs')
    parser.add_argument("--log_file",type=str,default='logs.json',help="input log file to be templated")
    parser.add_argument("--knowledge_file",type=str,default='knowledge.json',help="input knowledge file")
    parser.add_argument("--template_sel",type=float,default=1.2,help="select 1.1: template logs (not dstc10 task1); 1.2: template kb; 2: template dstc10 task1 logs")
    parser.add_argument("--output_file",type=str,default='output.txt',help="output templated file")
    
    args = parser.parse_args()

    if args.quick_selection==5:
        print('Running labels batch......')
        labels=['/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data/train/labels.json',
                '/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data/val/labels.json',
                '/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data_eval/test/labels.json',
                '/content/drive/MyDrive/Research/ner/alexa-with-dstc10-track2-dataset/task2/data/val/labels.json'
                
        ]
        kbs=['knowledge_mod.json',
             '/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data_eval/knowledge.json'
        ]
        outs=['DSTC9_task1_train_labels_template_PHONEME.json',
              'DSTC9_task1_val_labels_template_PHONEME.json',
              'DSTC9_task1_eval_labels_template_PHONEME.json',
              'DSTC9_track2_task2_labels_template_PHONEME.json'
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
        out=open('DSTC9_task1_train_log_templates.json','w')
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
    elif args.quick_selection==1.3:
        out=open('DSTC9_task1_val_log_templates.json','w')
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
        out=open('DSTC9_task1_kb_templates.json','w')
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
        out=open('DSTC9_task1_log_eval_templates.json','w')
        logs=open('/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data_eval/test/logs.json','r')
        data=json.load(logs)
        kb=open('/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data_eval/knowledge.json','r')
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
        out=open('DSTC9_task1_kb_eval_templates.json','w')
        kb=open('/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data_eval/knowledge.json','r')
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
    elif args.quick_selection==3:
        out=open('DSTC10_task1_log_templates.json','w')
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
        out=open('DSTC10_task2_log_templates.json','w')
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
    
    elif not args.testmode:
        out=open(args.output_file,'w')
        logs=open(args.log_file,'r')
        data=json.load(logs)
        kb=open(args.knowledge_file,'r')
        dic=json.load(kb)

        bt=BabyTrie()#setting up bt based on knowledge base
        if args.template_sel==1.1:
            bt.initialize(dic)
            print('Trie successfully initialized.')
            new_data=run_dstc9_log(bt,data)
        elif args.template_sel==1.2:
            bt.initialize(dic)
            print('Trie successfully initialized.')
            new_data=run_dstc9_kb(bt,dic)
        elif args.template_sel==2:
            bt.sp_initialize(dic)
            print('Special Trie successfully initialized.')
            new_data=run_dstc9_log(bt,data)
        
        logs.close()
        kb.close()

        print('dumping...')
        json.dump(new_data,out,indent=4)
        out.close()
        print('Done.')
    
    elif args.testmode:
        print('Using dstc10 task1 db to initialize bt:')
        kb=open('/content/drive/MyDrive/Research/ner/alexa-with-dstc10-track2-dataset/task1/data/db.json','r')
        dic=json.load(kb)
        bt=BabyTrie()#setting up bt based on knowledge base
        bt.sp_initialize(dic)
        print('(sp) Trie successfully initialized.')
        mode=input('Input testing mode; 1 for log style and 2 for kb style')
        sen=input('Input testing sentence. Input exit to stop.')
        while sen!='exit':
            if mode==1:
                print('Running test as |dstc9/dstc10| logs.json example...')
                print('\n')
                template,map=gettemplate_wmap(bt,sen)
                print('Template: ',template)
                print('Map: ',map)
            elif mode==2:
                print('Running test as |dstc9/dstc10_task2| knowledge.json example...')
                print('\n')
                template=getkbtemplate(bt,sen)
                print('Template: ',template)
            mode=input('Input another testing mode; 1 for log style and 2 for kb style')
            sen=input('Input another testing sentence. Input exit to stop.')
    
if __name__=='__main__':
    main()