import re

def gettemplate_wmap(bt,title):
    # title=convert_text2num(title).strip()
    word_lst,ind_dic=bt.isinTrie(title)
    nlst=[]
    new_sen=title.strip()#cleans up sentence
    plst=re.findall(r"[\w']+|[.,!?;]", new_sen) # premature list used for clean-up
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
            temp_str=temp_str[:-1] # getting rid of last space
            en_dic['<'+key+'-'+str(pair[1])+'>']=temp_str
            title=title.replace(temp_str,'<'+key+'-'+str(pair[1])+'>')
    return (title,en_dic)
