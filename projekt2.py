import time
from tqdm import tqdm

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
from matplotlib import rcParams
import seaborn as sns
sns.set_style("whitegrid")
rcParams.update({'figure.autolayout': True})

df = pd.read_csv("./clean_data.csv", sep = ";", low_memory = False)
#df.head()

vodniTipovi = [item for item in list(df.loc[:, "Vodi tip"].unique()) if item != ""]
kategorijePokazatelja = [item for item in list(df.loc[:, "Kategorija pokazatelja"].unique()) if item is not np.nan]

bioColumns = ["- EP [%]", "- EP-Taxa", "- EPT [%] (abundance classes)", "- EPT-Taxa", "- EPT-Taxa [%]", "- Ephemeroptera", "- Ephemeroptera [%]", "- Plecoptera", "- Plecoptera [%]", "- Trichoptera", "- Trichoptera [%]", "Abundance [ind/m2]", "BMWP Score", "Diversity (Margalef Index)", "Diversity (Shannon-Wiener-Index)", "Diversity (Simpson-Index)", "Evenness", "Number of Families", "Number of Genera", "Number of Taxa"]
nonBioColumns = [item for item in df.loc[:, "Pokazatelj"].unique() if item not in bioColumns]
newColumns = bioColumns + nonBioColumns

frame = df.copy()

def singlePerm(twoValFrame, nPerm):
    permArray = np.zeros(nPerm)
    for i in range(nPerm):
        col1 = list(twoValFrame.columns)[1]
        twoValFrame.loc[:, col1] = np.random.permutation(twoValFrame.loc[:, col1].values)
        permArray[i] = twoValFrame.corr().values[0, 1]
    return permArray.copy()
    

def corrPerm(dFrame, nPerm = 250):
    corrFrame = pd.DataFrame()
    cols = list(dFrame.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            corrFrame.loc[:, "corr({} ,{})".format(cols[i], cols[j])] = singlePerm(
                dFrame.loc[:, [cols[i], cols[j]]], nPerm)
    return corrFrame

alpha = 0.05
plotRange = [None] + vodniTipovi
for tip in tqdm(plotRange):
    if tip is not None:
        tmpFrame = frame.loc[frame.loc[:, "Vodi tip"] == tip]
    else:
        tmpFrame = frame
        tip = "Svi"
    
    ukupnoFrame = tmpFrame.pivot_table(values = "ukupno",
                                    columns="Pokazatelj", index = "Naziv postaje", aggfunc=np.sum)
    countFrame = tmpFrame.pivot_table(values = "br.an.",
                                   columns="Pokazatelj", index = "Naziv postaje", aggfunc=np.sum)
    meanFrame = ukupnoFrame / countFrame
    
    sampleNumber = len(meanFrame)
    if sampleNumber < 3:
        continue
    
    fig, axes = plt.subplots(2, 1, figsize = (45, 48))
    fig2, axes2 = plt.subplots(2, 1, figsize = (45, 48))
    fig3, ax3 = plt.subplots(figsize = (45, 24))
    dropFig, dropAx = plt.subplots(figsize = (45, 24))
    
    tmpCorr =  meanFrame.corr().applymap(lambda x: "{:.2f}".format(x)).astype(float)
    availableValues = [item for item in newColumns if item in tmpCorr.columns]
    
    pVals = tmpCorr.loc[availableValues, availableValues].copy()
    signif = tmpCorr.loc[availableValues, availableValues].copy()
    features = list(tmpCorr.columns)
    for i in tqdm(range(len(features)), leave = False):
        for j in tqdm(range(i + 1, len(features)), leave = False):
            corrVal = tmpCorr.loc[features[i], features[j]]
            permSamples = corrPerm(meanFrame.loc[:, [features[i], features[j]]])
            if np.isnan(corrVal):
                pVal = 1.0
            elif corrVal >= 0:
                pVal = (permSamples > corrVal).mean()[0]
            else:
                pVal = (permSamples < corrVal).mean()[0]
            pVals.loc[features[i], features[j]] = pVal
            pVals.loc[features[j], features[i]] = pVal
            signif.loc[features[i], features[j]] = float(pVal < alpha)
            signif.loc[features[j], features[i]] = float(pVal < alpha)
            
    sns.heatmap(tmpCorr, cmap = "inferno", ax = axes[0], annot = True)
    sns.heatmap(pVals, cmap = "inferno", ax = axes[1], annot = True)
    
    sns.heatmap(tmpCorr, cmap = "inferno", ax = axes2[0], annot = True)
    sns.heatmap(signif, cmap = "inferno", ax = axes2[1], annot = True)
    
    tmpCorr.fillna(0, inplace = True)
    signif.fillna(0, inplace = True)
    
    sns.heatmap(tmpCorr, cmap = "inferno", ax = dropAx, annot = True)
    sns.heatmap(signif, cmap = "inferno", ax = ax3, annot = True)
    
    
    
    
    def corrTrans(value):
        if value == "250.0":
            return " "
        else:
            return value
    
    for t1, t2 in zip(ax3.texts, dropAx.texts):
        t1.set_text(corrTrans(t2.get_text()))
    
    axes[0].set_title("Vodni tip: {}\nBroj uzoraka: {}".format(tip, sampleNumber))
    axes[1].set_title("p-vrijednost")
    fig.savefig("./pics/corrPermTest/corrPlot_{}.pdf".format(tip))
    #plt.show(fig)
    plt.close(fig)
    
    axes2[0].set_title("Vodni tip: {}\nBroj uzoraka: {}".format(tip, sampleNumber))
    axes2[1].set_title("značajnost")
    fig2.savefig("./pics/corrPermTest/corrPlotsignif_{}.pdf".format(tip))
    #plt.show(fig2)
    plt.close(fig2)
    
    ax3.set_title("Vodni tip: {}\nBroj uzoraka: {}".format(tip, sampleNumber))
    fig3.savefig("./pics/corrMerge/corrPlot_{}.pdf".format(tip))
    #plt.show(fig3)
    plt.close(fig3)
    #plt.show(dropFig)
    plt.close(dropFig)