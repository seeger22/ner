import torch
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification, AutoConfig
import string
import json
import pickle
from tqdm import tqdm


def main():  
    def _get_title_body_pair(kb, doc_id):
        #gets title_ex and body_ex
        cat,id,d_id = doc_id.split('_')
        body_ex = kb[cat][id]['docs'][d_id]['body_ex']
        title_ex = kb[cat][id]['docs'][d_id]['title_ex']
        return (title_ex, body_ex)
    
    def __convert_to_tgt(domain, entity, pair):
        field_names = ["[DOMAIN]", "[ENTITY]", "[TITLE]", "[BODY]"]
        field_values = [domain]
        if entity is not None:
            field_values.append(entity)
        else:
            field_values.append("*")
        field_values.append(" ".join(pair[0].split()))
        field_values.append(" ".join(pair[1].split()))
    
        fields = [name + " " + value for name, value in zip(field_names, field_values)]
        return " ".join(fields)
    
    def single_test(title,k):
        result = tokenizer(title, return_tensors="pt")
        result.to(device)
        model.eval()
        outputs = model(**result)
        predictions = torch.topk(outputs.logits,k)
        torch.cuda.empty_cache()
        return predictions

    f1 = open('/content/drive/MyDrive/Research/ner/intent_classifier/DSTC10_clean_val_logs.json','r')
    log = json.load(f1)
    f1.close()

    f2 = open('predict.json','r')
    label = json.load(f2)
    f2.close()

    f3 = open('/content/drive/MyDrive/Research/ner/intent_classifier/final_result/kb_eval_final.json','r')
    kb = json.load(f3)
    f3.close()
    
    f4 = open('/content/drive/MyDrive/Research/ner/text_classifier/final_results/finale.pkl','rb')
    cluster = pickle.load(f4)
    f4.close()

    id_to_name_map = {}

    for cat in kb:
        for elem in kb[cat]:
            doc_lst = kb[cat][elem]['docs']
            name = kb[cat][elem]['name']
            for entry in doc_lst:
                id = doc_lst[entry]['doc_id']
                if id in id_to_name_map:
                    print('What')
                else:
                    id_to_name_map[id] = name

    model_name = "bert-base-uncased"
    batch_size = 32
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    config = AutoConfig.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True, padding = True, truncation = True)
    model = AutoModelForSequenceClassification.from_pretrained("fdstc10_intent_MT1_3")
    
    # Set device
    model.to(device)
    
    n = 0
    out = open('prediction_set_1.txt','w')
    out.write("src\ttgt\n")
    
    for i in range(len(log)):
        if label[i]['target'] == 1:
            dialog = []
            entity_lst = label[i]['ne_rank']
            for turn in log[i]:
                dialog.append(f"{turn['text']}\x01{1 if turn['speaker'] == 'U' else 0}")
            dialog = " [SEP] ".join(dialog)
            cluster_ids = single_test(turn['text'],3)[1][0]
            if 0 in cluster_ids:
                cluster_ids = single_test(turn['text'],4)[1][0]
            for cluster_id in cluster_ids:
                if cluster_id == 0:
                    continue
                for doc_id in cluster[int(cluster_id)]:
                    entity_name = id_to_name_map[doc_id]
                    for entry in entity_lst:
                        entity = entry['entity_name']
                        if entity == entity_name:
                            n += 1
                            domain = doc_id.split('_')[0]
                            pair = _get_title_body_pair(kb, doc_id)
                            tgt = __convert_to_tgt(domain, entity, pair)
                            out.write(f"{dialog}\t{tgt}\1{0}\n")
                            print(entity, entity_name, sep='\t==\t')
    out.close()
    print(n)

if __name__ == "__main__":
    main()