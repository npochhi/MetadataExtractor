import xml.etree.ElementTree as ET
import unicodedata
import operator
import subprocess
import xml.dom.minidom
import re

directory = "OutputDirectory/"

def generateXML(tree, footnoteString):
	root = tree.getroot()
	chunkList = root.findall('chunk')
	newRoot = ET.Element("Footnotes")
	
	lineList = footnoteString.split('\n')
	count = 0

	for line in lineList:
		columnList = line.split('\t')

		if len(columnList) == 6 and columnList[5] == "FOOTNOTE":
			resultString = ''
			for token in chunkList[count].findall('token'):
				resultString += token.text + ' '
			resultStrList = resultString.strip('\n')
			ET.SubElement(newRoot, "footnote").text = resultStrList
		count += 1

	return newRoot

def footnoteMain(root, filename):
	footnoteString = ''
	maxFontSize = 0
	pYCoord = None 
	yCoordDiff = {}
	fontSizes = {}
	count = 0

	for page in root.findall('PAGE'):
		lastYCoord = 0
		for text in page.findall('TEXT'):
			for token in text.findall('TOKEN'):
				try:
					fontSizes[round(abs(float(token.attrib['font-size'])))] = fontSizes.get(round(abs(float(token.attrib['font-size']))), 0) + 1
					if pYCoord == None:
						pYCoord = float(token.attrib['y'])
					yCoordDiff[round(abs(float(token.attrib['y']) - lastYCoord))] = yCoordDiff.get(round(abs(float(token.attrib['y']) - lastYCoord)), 0) + 1
					lastYCoord = float(token.attrib['y'])
				except:
					errorVar = 1

	maxFontSize = 0

	for fSize in fontSizes.keys():
		if maxFontSize is 0:
			maxFontSize = fSize
			continue
		if fontSizes[fSize] > fontSizes[maxFontSize]:
			maxFontSize = fSize

	sortYDiffList = sorted(yCoordDiff.iteritems(), key = operator.itemgetter(1), reverse = True)[ : 7]
	tempList = []

	for yDiff in sortYDiffList:
		if(yDiff[0] > 6.0):
			tempList.append(yDiff)
	
	processedYDiffList = tempList
	tempList = []
	mode = processedYDiffList[0][1]

	for YDiff in processedYDiffList:
		if not(YDiff[1] <= mode / 2 or abs(processedYDiffList[0][0] - YDiff[0]) >= 4):
			tempList.append(YDiff)
	
	processedYDiffList = tempList

	del tempList

	limit = max([yDiff[0] for yDiff in processedYDiffList]) + 2
	newRoot = ET.Element("Document")
	chunk = ET.SubElement(newRoot, "chunk")

	for page in root.findall('PAGE'):
		for text in page.findall('TEXT'):
			for token in text.findall('TOKEN'):
				if type(token.text) is unicode:
					if len(token.text) == 1:
						if ord(token.text) == 8727:
							word = "*"
						elif ord(token.text) == 8224:
							word = "*"
						elif ord(token.text) == 8225:
							word = "*"
						elif ord(token.text) == 167:
							word = "*"
						elif ord(token.text) == 958:
							word = "*"
						elif ord(token.text) == 182:
							word = "*"
						else:
							word = unicodedata.normalize('NFKD', token.text).encode('ascii', 'ignore')
					else:          
						if len(token.text) == 1:
							pass
						word = unicodedata.normalize('NFKD', token.text).encode('ascii', 'ignore')
				else:
					word = token.text
				if word and len(word.replace(' ', '')) > 0:
					if abs(float(token.attrib['y']) - pYCoord) >= limit:
						chunk = ET.SubElement(newRoot, "chunk")
					pYCoord = float(token.attrib['y'])
					ET.SubElement(chunk, "token", y = token.attrib['y'], font_size = token.attrib['font-size'], bold = token.attrib['bold']).text = word
	
	tree = ET.ElementTree(newRoot)
	newXRoot = tree.getroot()

	for chunkStr in newXRoot.findall('chunk'):
		boldCount = 0
		fontSize = 0
		tokenCount = 0
		cond = None
		token = chunkStr.findall('token')

		if len(token) == 0:
			footnoteString += "x x 0 0 0 0\n"
			continue
		elif len(token) == 1:
			token1 = '$$$'
			token2 = token[0].text
			cond = token2
			yTok1 = yTok2 = token[0].attrib['y']
		else:
			token1 = token[0].text
			token2 = token[1].text
			cond = token1
			yTok1 = token[0].attrib['y']
			yTok2 = token[1].attrib['y']

		tokenCount = len(token)

		for tokenSamp in token:
			if tokenSamp.attrib['bold'] == "yes":
				boldCount += 1
			fontSize += float(tokenSamp.attrib['font_size'])
		
		boldCount /= tokenCount
		fontSize = (fontSize / tokenCount) / maxFontSize
			
		if cond == "Table" or cond == "TABLE" or cond == "Figure" or cond == "FIGURE" or cond == "Fig." or cond == "FIG.":
			firstWord = 1
		else:
			firstWord = 0

		pattern = re.compile('[^@]+@[^@]+\.[^@]+')

		if type(pattern.match(token2)) == type(pattern.match('yano@k.u-tokyo.ac.jp')):
			isEmail = 1
		else:
			isEmail = 0

		if yTok1 > 400 and tokenCount >= 2 and (token1.isdigit() or token1 == "*" ) and (yTok1 < yTok2) and  (token2[0 : 3] == "www" or token2[0:4] == "http" or token2 == "A" or isEmail==1 or (len(token2) > 1 and (token2.strip(',-:;')).isalpha() and token2[0].isupper())):
			isFootnote = "FOOTNOTE"
		else:
			isFootnote = "0"

		yPos = token[0].attrib['y']

		footnoteString += token1+"\t"+token2+"\t"+str(round(fontSize,2))+"\t"+str(yPos)+"\t"+str(firstWord)+"\t"+(isFootnote)+"\n"	
	XMLCode = generateXML(tree, footnoteString)
	XMLCodeStr = ET.tostring(XMLCode, 'utf-8')
	reparsedXMLCode = xml.dom.minidom.parseString(XMLCodeStr)

	with open(directory + filename + "_FOOTNOTE.xml", "w") as XMLFile:
		XMLFile.write(reparsedXMLCode.toprettyxml(indent = "\t"))
