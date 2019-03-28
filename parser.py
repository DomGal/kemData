import json
import time
from tqdm import tqdm
import pandas as pd
import numpy as np


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

def floatify(value):
    try:
        floatVal = float(value)
        return floatVal
    except:
        return np.nan


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

    with open("./temp_data.dat", "w") as outFile:
        outFile.write("[\n")

    with open("./temp_data.dat", "a") as outFile:
        for dataPoint in AllDataList[:-1]:
            outFile.write(dataPoint + ",\n")
        outFile.write(AllDataList[-1] + "\n]")

    df = pd.read_json("./temp_data.dat")

    df = df.loc[df.loc[:, "Kategorija pokazatelja"].notna()]
    df.loc[:, "SR.VR."] = df.loc[:, "SR.VR."].apply(lambda x: "".join(x.split(",")) if len(x.split()) <=2 else np.nan).apply(lambda x: np.nan if x == "" else x).apply(floatify)

    df = df.loc[df.loc[:, "SR.VR."].notna()]

    df.loc[:, "br.an."] = df.loc[:, "br.an."].astype(float)
    df.loc[:, "ukupno"] = df.loc[:, "br.an."] * df.loc[:, "SR.VR."]


    metaColumns = ["Datum ispisa", "Naziv postaje", "Medij", "Mikrolokacija", "Razdoblje", "Vodi tip", "godina", "Šifra postaje"]

    auxColumns = ["10%", "50%", "90%", "Kategorija pokazatelja", "MAX", "MIN", "Pokazatelj", "SR.VR.", "ST.DEV.", "ukupno", "br.an."]

    bioColumns = ["- EP [%]", "- EP-Taxa", "- EPT [%] (abundance classes)", "- EPT-Taxa", "- EPT-Taxa [%]", "- Ephemeroptera", "- Ephemeroptera [%]", "- Plecoptera", "- Plecoptera [%]", "- Trichoptera", "- Trichoptera [%]", "Abundance [ind/m2]", "BMWP Score", "Diversity (Margalef Index)", "Diversity (Shannon-Wiener-Index)", "Diversity (Simpson-Index)", "Evenness", "Number of Families", "Number of Genera", "Number of Taxa"]

    chemFrame = df.loc[:, metaColumns + auxColumns]

    bioFrameList = []
    bioFrame = df.loc[:, bioColumns + metaColumns]
    for bioValue in tqdm(bioColumns):
        tmpFrame = bioFrame.loc[:, [bioValue] + metaColumns].copy()
        tmpFrame.loc[:, "Pokazatelj"] = bioValue
        tmpFrame.loc[:, "br.an."] = 1
        tmpFrame.loc[:, "Kategorija pokazatelja"] = "Biološki pokazatelji"
        
        tmpFrame.loc[:, bioValue] = tmpFrame.loc[:, bioValue].apply(lambda x: "".join(x.split(",")) if len(x.split()) <=2 else np.nan).apply(lambda x: np.nan if x == "" else x).apply(floatify)

        tmpFrame.columns = ["ukupno"] + list(tmpFrame.columns[1:])
        
        bioFrameList.append(tmpFrame.copy())

    bioMerged = pd.concat(bioFrameList, ignore_index=True, sort = False)

    mergedFrame = pd.concat([chemFrame, bioMerged], ignore_index=True, sort = False)

    mergedFrame.to_csv(outFilePath, sep = ";", index = False)
    
    return None


if __name__ == "__main__":
    main("./raw_data.csv", "./clean_data.csv")
    print("done")