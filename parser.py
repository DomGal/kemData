import json

metadata_config = ["Naziv postaje", "Šifra postaje", "Razdoblje", "Medij", "Datum ispisa", "Mikrolokacija"]
feature_config = ["Fizikalno kemijski pokazatelji", "Režim kisika", "Hranjive tvari", "Metali", "Organski spojevi", "Ioni"]

def preprocess(line):
    lineList = ["" if item == "#N/A" else item.strip() for item in line.strip().split(";")]
    return lineList

def shouldDicard(lineList):
    lineSet = set(lineList)
    if (len(lineSet.difference(set([""]))) == 0):
        return True
    if lineList[0].lower() == "pokazatelj":
        return True
    return False
    
def isMetaData(lineList, config = metadata_config):
    metaDict = dict()
    for item in lineList:
        for metaItem in config:
            if metaItem in item:
                key, value = item.split(":")
                metaDict[key.strip()] = value.strip()
    return len(metaDict) > 0, metaDict

def isFeature(lineList, config = feature_config):
    featureDict = dict()
    for item in lineList:
        for feature in config:
            if feature in item:
                featureDict["Kategorija pokazatelja"] = item
                return True, featureDict
    return False, dict()

def extractData(lineList, columns):
    dataDict = {key : value for key, value in zip(columns, lineList) if key != ""}
    return dataDict

def shouldReset(lineList):
    for item in lineList:
        if "statistika" in item.lower():
            return True
    return False

def main(inFilePath, outFilePath):
    AllDataList = []
    with open(inFilePath) as f:
        lines = f.readlines()

    metaDict = dict()
    for lineNumber, line in enumerate(lines):
        lineList = preprocess(line)
        
        if lineNumber == 0:
            columns = lineList
        
        if shouldDicard(lineList):
            continue
        
        metaIndicator, metaUpdate = isMetaData(lineList)
        featureIndicator, featureUpdate = isFeature(lineList)

        if shouldReset(lineList):
            metaDict.clear()
            continue
        
        if metaIndicator:
            metaDict.update(metaUpdate)
            continue
            
        if featureIndicator:
            metaDict.update(featureUpdate)
            continue
            
        dataDict =  extractData(lineList, columns)
        dataDict.update(metaDict)

        jsonData = json.dumps(dataDict)
        AllDataList.append(jsonData)

    with open(outFilePath, "w") as outFile:
        outFile.write("[\n")

    with open(outFilePath, "a") as outFile:
        for dataPoint in AllDataList[:-1]:
            outFile.write(dataPoint + ",\n")
        outFile.write(AllDataList[-1] + "\n]")
    
    return None


if __name__ == "__main__":
    main("./raw_data.csv", "./clean_data.dat")
    print("done")