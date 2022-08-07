import re

def simple_num2words(int):
    lst=['zero','one','two','three','four','five','six','seven','eight',
         'nine']
    return lst[int]

def is_number(x):
    if type(x) == str:
        x = x.replace(',', '')
    try:
        float(x)
    except:
        return False
    return True

def convert_text2num (textnum, numwords={}):
    units = [
        'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
        'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
        'sixteen', 'seventeen', 'eighteen', 'nineteen',
    ]
    tens = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
    scales = ['hundred', 'thousand', 'million', 'billion', 'trillion']
    ordinal_words = {'first':1, 'second':2, 'third':3, 'fifth':5, 'sixth':6, 'seventh':7, 'eighth':8, 'ninth':9, 'twelfth':12}
    
    #ordinal_endings = [('ieth', 'y'), ('th', '')]
    
    if not numwords:
        numwords['and'] = (1, 0)
        for idx, word in enumerate(units): numwords[word] = (1, idx)
        for idx, word in enumerate(tens): numwords[word] = (1, idx * 10)
        for idx, word in enumerate(scales): numwords[word] = (10 ** (idx * 3 or 2), 0)

    #textnum = textnum.replace('-', ' ')

    current = result = 0
    curstring = ''
    onnumber = False
    lastunit = False
    lastscale = False

    def is_numword(x):
        if is_number(x):
            return True
        if word in numwords:
            return True
        return False

    def from_numword(x):
        if is_number(x):
            scale = 0
            increment = int(x.replace(',', ''))
            return scale, increment
        return numwords[x]

    word_lst=re.findall(r"[\w']+|[.,!?;]", textnum)
    last=len(word_lst)-1
    for i in range(len(word_lst)):
        word=word_lst[i]
        if word in ordinal_words:
            scale, increment = (1, ordinal_words[word])
            current = current * scale + increment
            if scale > 100:
                result += current
                current = 0
            onnumber = True
            lastunit = False
            lastscale = False
            print(result)
        else:
            '''
            for ending, replacement in ordinal_endings:
                if word.endswith(ending):
                    word = "%s%s" % (word[:-len(ending)], replacement)
            '''
            if (not is_numword(word)) or (word == 'and' and not lastscale):
                if onnumber:
                    # Flush the current number we are building
                        curstring += repr(result + current)+' '
                if (not word.isalnum()) and (len(word)==1):
                    curstring=curstring[:-1]
                curstring += word+" "
                result = current = 0
                onnumber = False
                lastunit = False
                lastscale = False
            else:
                scale, increment = from_numword(word)
                onnumber = True

                if lastunit and (word not in scales):                                                                                                                                                                                                                                         
                    # Assume this is part of a string of individual numbers to                                                                                                                                                                                                                
                    # be flushed, such as a zipcode "one two three four five"                                                                                                                                                                                                                 
                    curstring += repr(result + current)                                                                                                                                                                                                                                       
                    result = current = 0                                                                                                                                                                                                                                                      

                if scale > 1:                                                                                                                                                                                                                                                                 
                    current = max(1, current)                                                                                                                                                                                                                                                 

                current = current * scale + increment                                                                                                                                                                                                                                         
                if scale > 100:                                                                                                                                                                                                                                                               
                    result += current                                                                                                                                                                                                                                                         
                    current = 0                                                                                                                                                                                                                                                               

                lastscale = False                                                                                                                                                                                                              
                lastunit = False                                                                                                                                                
                if word in scales:                                                                                                                                                                                                             
                    lastscale = True                                                                                                                                                                                                         
                elif word in units:                                                                                                                                                                                                             
                    lastunit = True

    if onnumber:
        curstring += repr(result + current)

    return curstring