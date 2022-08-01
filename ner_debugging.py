import json


x=open('DSTC10_track2_task2_log_phon_templates.json','r')
y=open('/content/drive/MyDrive/Research/ner/alexa-with-dstc10-track2-dataset/task2/data/val/labels.json','r')
log=json.load(x)
label=json.load(y)

i=0#keep track of which element in log/label (dialogue number)
n=0#number of edge cases
edge_cases=[]

for dialogue in label:
    if dialogue['target']==True:

        c=False
        id_flag=False
        cat_flag=False
        log_dialogue=log[i]

        target_id=str(dialogue['knowledge'][0]['entity_id'])
        target_cat=dialogue['knowledge'][0]['domain']
        for turn in log_dialogue:
            for entity_id in turn['id_map']:
                entity_id=entity_id[1:-1]
                cat,id=entity_id.split('-')
                if '|' in id:
                    c=True
                    print('Chained Restaurant Problem')
                    ids=id.split('|')
                    for pos in ids:
                        if id==target_id:
                            id_flag=True
                else:
                    if id==target_id:
                        id_flag=True
                if cat==target_cat:
                    cat_flag=True
        if (not id_flag) and (not cat_flag):
            case={}
            case['entity_id']='-'.join([target_cat,target_id])
            case['dialogue']=log_dialogue
            edge_cases.append(case)
            if c:
                print('Chained Restaurant Problem')
            else:
                print('Problem #',n)
            n+=1
        i+=1

out=open('DSTC10_track2_task2_log_edgecases.json','w')
json.dump(edge_cases,out,indent=4)