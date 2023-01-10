import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize

import sys
import string
import re
  
def Clean_Text(text):
  text = re.sub(r'\\n', " ", text)
  text = re.sub(r'\\t', " ", text)
  return text
  
def Word_Tokenize(text):
  tokens = word_tokenize(text)
  ss = text.split()
  i = 0
  z = []
  left = ""
  for w in tokens:
    if i < len(ss) and w == ss[i]:
      z.append(w)
      i += 1
    elif w in string.punctuation:
      if left:
        # put the split word
        z.append(left)
        # clear
        left = ""
        # move to the next original token in ss
        i += 1
      # put the split punctuation
      z.append(w)
    else:
      # glue w into left
      left += w
      if i < len(ss) and left == ss[i]:
        # put the glued word like did n't -> didn't
        z.append(left)
        # clear
        left = ""
        # move to the next original token in ss
        i += 1
      else:
        z.append(left)
        left = ""
  return z

if __name__ == '__main__':
  for line in sys.stdin:
    line = Clean_Text(line.strip())
    print(" ".join(Word_Tokenize(line)))
