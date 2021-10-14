import os
import re
import snap
import random

path = 'fluidization-6991'

def readLiteraturesInOneFloder(folderPath):
	refList = []
	refInfo = {}

	filenames = os.listdir(path)
	for filename in filenames:
		with open(path+'/'+filename,'rb') as f:
			lines = f.readlines()
			#print(str(lines, encoding="utf-8")[:1000].split('and'))
			for line in lines:
				content = str(line, encoding="utf-8").replace('\n','')

				if content=='':
					continue
				elif content=='EF':
					break
				if not re.match('  ',content):
					#遇到关键字PT创建新的文献字典
					if re.match('PT',content):
						refInfo = {}			
					#遇到关键字ER说明本文献记录完毕，添加到refList中
					elif re.match('ER',content):
						refList.append(refInfo)
					else:
						contentList = content.split(' ',1)
						keyWord = contentList[0]
						keyValue = contentList[1]
						refInfo[keyWord] = [keyValue]
						flag = keyWord
				else:
					content = content.lstrip()
					refInfo[flag].append(content)

				#遇到关键字ER说明本文献记录完毕，添加到refList中
				#if re.match('ER',content):
					#refList.append(refInfo)
	return refList

def extractRefInfo(refInfo):
	#从refInfo中提取DOI信息
	doi = refInfo['DI'][0]

	#从refInfo中提取TITLE信息
	title = ''
	for i in range(len(refInfo['TI'])):
		addBlank = ''
		if i>0:
			addBlank = ' '
		title += addBlank+refInfo['TI'][i]
		title = title.replace('\"','\'')#这里主要是处理一些回复或者校错类的文章，标题里面本身带双引号，影响后面csv输出格式

	#从refInfo中提取AUTHOR信息
	author = ';'.join(refInfo['AF']).replace(',','')

	return doi, title, author

if __name__=='__main__':
	#1.读取数据
	print("reading data...")
	refList = readLiteraturesInOneFloder(path)
	print('reading data finished, load',len(refList),'references')

	#2.对得到的文献数据进行处理，仅保留含有DOI的文献
	#对于fluidization，没有doi的文章共381(总数为6991)
	print('check if ref has doi...')
	refListDOI = []
	for i in range(len(refList)):
		if 'DI' in refList[i]:
			refListDOI.append(refList[i])
	print(len(refListDOI),'refs with doi are saved in refListDOI')

	#3.构建网络节点，同时构建{(doi,NodeId)}的字典-DicDoiNodeId
	print('construct refNetwork Nodes...')
	DicDoiNodeId = {}
	refNetwork = snap.TNEANet.New()
	for i in range(len(refListDOI)):
		refNetwork.AddNode(i)
		doi, title, author = extractRefInfo(refListDOI[i])
		refNetwork.AddStrAttrDatN(i, doi, 'doi')
		refNetwork.AddStrAttrDatN(i, title, 'title')
		refNetwork.AddStrAttrDatN(i, author, 'author')
		DicDoiNodeId[doi] = i
	print('refNetwork Nodes construction finished')

	#4.构建网络边******************************************************先采用随机边
	'''
	count = 0
	for i in range(len(refListDOI)):
		if 'CR' not in refListDOI[i]:
			print('i=',i,'doi=',refListDOI[i]['DI'][0])
			count += 1
	print('count:',count)
	'''

	print('construct refNetwork Edges...')
	for i in range(len(refListDOI)):
		if 'CR' in refListDOI[i]:
			CRs = refListDOI[i]['CR']
			for j in range(len(CRs)):
				if 'DOI ' in CRs[j]:
					CRDoi = CRs[j].split('DOI ')[1]
					if CRDoi in DicDoiNodeId:
						citeNodeId = DicDoiNodeId[CRDoi]
						refNetwork.AddEdge(i,citeNodeId)
	print('refNetwork Edges construction finished')
	
	#5.计算网络的PageRank值
	print('PageRank refNetwork...')
	PRankH = snap.TIntFltH()
	snap.GetPageRank(refNetwork,PRankH)
	print('PageRank finished...')

	#6.排序PageRank结果
	print('sort PageRank result...')
	PRankDic = {}
	for key in PRankH:
		PRankDic[key] = PRankH[key]
	PRankH_order = sorted(PRankDic.items(),key=lambda x:x[1],reverse=True)
	print('sort PageRank result finished')

	#7.构建{(NodeId,inDegree)}的字典-DicNodeIdInDegree
	DicNodeIdInDegree = {}
	for NI in refNetwork.Nodes():
		id = NI.GetId()
		inDegree = NI.GetInDeg()
		DicNodeIdInDegree[id] = inDegree
	#8.将PageRank结果写入文件中
	print('writing result...')
	with open('PageRankResult.csv','w') as fp:
		line = 'PageRankNum,PageRankScore,title,doi,author,inDegree,NodeId'+'\n'
		fp.write(line)
		for i in range(len(PRankH_order)):
			PageRankNum = i+1
			NodeId = PRankH_order[i][0]
			PageRankScore = PRankH_order[i][1]
			title = '"'+refNetwork.GetStrAttrDatN(NodeId,'title')+'"'
			doi = '"'+refNetwork.GetStrAttrDatN(NodeId,'doi')+'"'
			author = '"'+refNetwork.GetStrAttrDatN(NodeId,'author')+'"'
			inDegree = DicNodeIdInDegree[NodeId]
			line = str(PageRankNum)+','+str(PageRankScore)+','+title+','+doi+','+author+','+str(inDegree)+','+str(NodeId)+'\n'
			fp.write(line)
	print('file write finished')


	'''
	print(PRankH_order[0],':')
	print(refNetwork.GetStrAttrDatN(PRankH_order[0][0],'title'))
	print(refNetwork.GetStrAttrDatN(PRankH_order[0][0],'doi'))
	print(refNetwork.GetStrAttrDatN(PRankH_order[0][0],'author'))
	print(PRankH_order[1],':')
	print(refNetwork.GetStrAttrDatN(PRankH_order[1][0],'title'))
	print(refNetwork.GetStrAttrDatN(PRankH_order[1][0],'doi'))
	print(refNetwork.GetStrAttrDatN(PRankH_order[1][0],'author'))
	

	print(DicDoiNodeId['10.1016/j.ijmecsci.2019.105373'])
	print('10.1016/j.ijmecsci.2019.105373' in DicDoiNodeId)
	print('10.1016/j.ijmecsci.2019.1053731' in DicDoiNodeId)
	print(DicDoiNodeId['10.1016/j.ijmecsci.2019.1053731'])

	print(refList[0]['CR'][1])
	print(refList[0]['CR'][1].split('DOI ')[1])
	'''