import codecs
import re

input_data = codecs.open('/home/zju/xlc/bert/bert-master/addressData/finalData.txt','r','utf-8')
output_data = codecs.open('/home/zju/xlc/bert/bert-master/addressData/vocNum.txt','w','utf-8')
exist_sq = []
for line in input_data.readlines():
    vocTemp = re.findall(r"\d+", line)
    if vocTemp != []:
        isExist = False
        for shequItem in exist_sq:
            if vocTemp[0] == shequItem:
                isExist = True
        if isExist == False:
            exist_sq.append(vocTemp[0])
for shequItem in exist_sq:
    output_data.write(shequItem+"\n")
output_data.close()
input_data.close()

