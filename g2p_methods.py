from g2p_en import G2p
import json

def g2p_log(logfile,outfile):
    g2p = G2p()
    out=open(outfile,'w')
    data=open(logfile,'r')
    logs=json.load(data)
    data.close()

    n=0
    for dialogue in data:
        for section in dialogue:
            if section['text'] is not None:
                phoneme=g2p(section['text'])
                section['phoneme']=phoneme
            n+=1
            print('line/execution #',n)

    print('dumping...')
    json.dump(logs,out,indent=4)
    out.close()
    print('Done.')


def g2p_kb(kb_file,outfile):
    g2p = G2p()
    out=open(outfile,'w')
    kb=open(kb_file,'r')
    dic=json.load(kb)
    kb.close()

    n=0
    for cat in dic:
        for num in dic[cat]:
            entity=dic[cat][num]['name']
            if not entity:#skip the taxi stuff
                continue
            sen_dic=dic[cat][num]['docs']
            for entry in sen_dic:
                if sen_dic[entry]['title'] is not None:
                    title_phoneme=g2p(sen_dic[entry]['title'])
                    sen_dic[entry]['title_phoneme']=title_phoneme
                if sen_dic[entry]['title'] is not None:
                    body_phoneme=g2p(sen_dic[entry]['body'])
                    sen_dic[entry]['body_phoneme']=body_phoneme
                print('line/execution #',n)
                n+=1

    print('dumping...')
    json.dump(dic,out,indent=4)
    out.close()
    print('Done.')

def main():
    '''INFO
    OUTPUT -> REFERENCED INPUT

    DSTC9:
    'PHONEME_DSTC9_task1_train_log_templates.json' -> 'logs_mod.json' (train)
    'PHONEME_DSTC9_task1_val_log_templates.json' -> '/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data/val/logs.json' (val)
    'PHONEME_DSTC9_task1_kb_templates.json' -> 'knowledge_mod.json' (kb)

    DSTC10:
    'PHONEME_DSTC9_task1_log_eval_templates.json' -> '/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data_eval/test/logs.json' (test/eval from dstc9)
    'PHONEME_DSTC9_task1_kb_eval_templates.json' -> '/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data_eval/knowledge.json' (kb_test/eval from dstc9)
    'PHONEME_DSTC10_task2_log_templates.json' -> '/content/drive/MyDrive/Research/ner/alexa-with-dstc10-track2-dataset/task2/data/val/logs.json' (val)
    '''

    log_outfiles=['PHONEME_DSTC9_task1_train_log_templates.json','PHONEME_DSTC9_task1_val_log_templates.json','PHONEME_DSTC9_task1_log_eval_templates.json','PHONEME_DSTC10_task2_log_templates.json']
    log_files=['logs_mod.json','/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data/val/logs.json','/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data_eval/test/logs.json',
               '/content/drive/MyDrive/Research/ner/alexa-with-dstc10-track2-dataset/task2/data/val/logs.json']
    for i in range(len(log_outfiles)):
        g2p_log(log_files[i],log_outfiles[i])
        print('DONE WITH LOG              #',i)
    print('DONE WITH LOGS--------------------------------------------------------------')

    kb_outfiles=['PHONEME_DSTC9_task1_kb_templates.json','PHONEME_DSTC9_task1_kb_eval_templates.json']
    kb_files=['knowledge_mod.json','/content/drive/MyDrive/Research/ner/huggingface/alexa-with-dstc9-track1-dataset/data_eval/knowledge.json']
    for i in range(len(kb_outfiles)):
        g2p_kb(kb_files[i],kb_outfiles[i])
        print('DONE WITH KNOWLEDGE              #',i)
    print('DONE WITH KNOWLEDGE--------------------------------------------------------------')

if __name__=='__main__':
    main()