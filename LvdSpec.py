import os
import os.path
from os import listdir
from pathlib import Path

from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import fileinput

import shutil
import subprocess
import sys
import webbrowser

import xml.etree.ElementTree as ET
import yaml
import configparser

import re
reAlpha='[^0-9,.-]'
def GetStringAsNumber(value):
    value = re.sub(reAlpha, '', value)
    #If empty, return
    if (value==""): return -1,False
    try:
        value=float(value)
        return value,True
    except:
        return -1,False

import math

#create ui for program
root = Tk()
root.programName="LVD Spec"
root.title(root.programName)
icon = os.getcwd() +"/icon.ico"
if os.path.isfile(icon):
    root.iconbitmap(icon)
root.withdraw()
root.UnsavedChanges=False


# Check if yaml is installed
package_name = 'yaml'

import importlib.util
spec = importlib.util.find_spec(package_name)
if spec is None:
    print(package_name +" is not installed")
    #subcall = ["pip install"+package_name]
    #with open('output.txt', 'w+') as stdout_file:
    #    process_output = subprocess.run(subcall, stdout=stdout_file, stderr=stdout_file, text=True)
    #    print(process_output.__dict__)
    #spec = importlib.util.find_spec(package_name)
    #if spec is None:
    messagebox.showerror(root.programName,"Please install "+package_name+" to use this program!")
    root.destroy()
    sys.exit("User does not have "+package_name)



#truncate strings for labels
def truncate(string,direciton=W,limit=20,ellipsis=True):
    if (len(string) < 3):
        return string
    text = ""
    addEllipsis = "..." if (ellipsis and (len(string)>limit)) else ""
    if direciton == W:
        text = addEllipsis+string[len(string)-limit:len(string)]
    else:
        text = string[0:limit]+addEllipsis
    return text
#Why isn't this built in?
def clamp(val, minval, maxval):
    if val < minval: return minval
    if val > maxval: return maxval
    return val



config = configparser.ConfigParser()
defaultConfig = configparser.ConfigParser()
defaultConfig['DEFAULT'] = {
    'parcelDir' : "",
    'arcDir' : "",
    'yamlvd' : "",
    'stageParamsLocation' : "",
    'levelFile' : ""
    }
def CreateConfig():
    print("creating valid config")
    with open('config.ini', 'w+') as configfile:
        defaultConfig.write(configfile)
    config.read('config.ini')

#create a config if necessary
if (not os.path.isfile(os.getcwd() + r"\config.ini")):
    CreateConfig()
config.read('config.ini')


def UpdateTitle(newtitle=""):
    prefix="*" if root.UnsavedChanges else ""
    workspace= os.path.basename(root.workspace)
    if (workspace.lower()=="workspace"):
        workspace=""
    else:
        workspace = "("+workspace+")"

    if (newtitle!=""):
        newtitle = " - "+newtitle

    root.title(prefix+root.programName+workspace+newtitle)

def UpdateTitleAuto():
    filename = os.path.basename(root.levelFile)
    newtitle = root.stageName+": "+filename
    UpdateTitle(newtitle)

root.arcDir = config["DEFAULT"].get("arcDir","")
root.stageParamsFolderShortcut = r"/stage/common/shared/param/"

#make sure that it is a validated parcel folder, otherwise quit
def IsValidParcel():
    #Is this the directory with Parcel.exe?
    return (os.path.exists(root.parcelDir + r"/parcel.exe"))

def SetParcel():
    messagebox.showinfo(root.programName,"Set Parcel directory")
    root.parcelDir = filedialog.askdirectory(title = "Select your Parcel directory")
    if (root.parcelDir == ""):
        root.destroy()
        sys.exit("Invalid folder")
    if (IsValidParcel() == False):
        messagebox.showerror(root.programName,"Please select the root of your Parcel folder")
        root.destroy()
        sys.exit("Invalid Folder")

#make sure that it is a validated arc folder, otherwise quit
def IsValidArc():
    #Is this the directory with ArcExplorer.exe?
    if (os.path.exists(root.arcDir + r"/ArcExplorer.exe")):
        #Has stageParams been extracted?
        if (os.path.exists(root.arcDir + r"/export" + root.stageParamsFolderShortcut + "groundconfig.prc")):
            return True
        else:
            messagebox.showerror(root.programName,"Please extra the folder stage/common/shared/param")
            root.destroy()
            sys.exit("Needs Param Folder")
    return False

#Get Stage Params folder from Valid Arc
def SetStageParams():
    #First, check to see if ArcExplorer Exists
    messagebox.showinfo(root.programName,"Set ArcExplorer directory")
    root.arcDir = filedialog.askdirectory(title = "Select your ArcExplorer directory")
    if (root.arcDir == ""):
        root.destroy()
        sys.exit("Invalid folder")
    if (IsValidArc() == False):
        messagebox.showerror(root.programName,"Please select the root of your ArcExplorer folder")
        root.destroy()
        sys.exit("Invalid Folder")

    root.stageParams = root.arcDir + r"/export"+ root.stageParamsFolderShortcut
    #Copy prc for our working file
    shutil.copy(root.stageParams + "groundconfig.prc", root.workspace+"/groundconfig.prc")

def SetYamlvd():
    messagebox.showinfo(root.programName,"Set Yamlvd directory")
    root.yamlvd = filedialog.askdirectory(title = "Select your Yamlvd directory")
    if (root.yamlvd == ""):
        root.destroy()
        sys.exit("Invalid folder")
    root.yamlvd = root.yamlvd + r"/yamlvd.exe"
    if (os.path.exists(root.yamlvd) == False):
        messagebox.showerror(root.programName,"Please select the root of your Yamlvd folder")
        root.destroy()
        sys.exit("Invalid Folder")


#make sure that it is a validated destination folder, otherwise quit
def IsValidModFolder():
    root.modDirName = os.path.basename(root.modDir)
    if (root.modDirName == "stage"):
        return False
    else:
        subfolders = [f.path for f in os.scandir(root.modDir) if f.is_dir()]
        for dirname in list(subfolders):
            if (os.path.basename(dirname) == "stage"):
                return True
    return False

#open folder dialogue
def SetWorkspace():
    quitOnFail=False
    newWorkspace = filedialog.askdirectory(title = "Select your workspace folder")
    if (newWorkspace == ""):
        return
    root.workspace = newWorkspace
    if (not os.path.exists(root.workspace+"/groundconfig.prc")):
        if (IsValidArc() == False):
            messagebox.showerror(root.programName,"FATAL: groundconfig.prc missing from StageParams")
            root.destroy()
            sys.exit("Invalid Folder")
        shutil.copy(root.stageParams + "groundconfig.prc", root.workspace+"/groundconfig.prc")

    UpdateTitleAuto()
    config.set("DEFAULT","workspace",root.workspace)
    with open('config.ini', 'w+') as configfile:
        config.write(configfile)
        

#Get or Set workspace
root.workspace = config["DEFAULT"].get("workspace","")
if (root.workspace == ""):
    print("no workspace")
    root.workspace = os.getcwd() +"/workspace"
    if (not os.path.exists(root.workspace)):
        os.makedirs(root.workspace)

#Set Parcel Directory if needed
root.parcelDir = config["DEFAULT"].get("parcelDir","")
if (not os.path.isdir(root.parcelDir)):
    root.parcelDir = ""
#Get or Set root.parcelDir
if (root.parcelDir == ""):
    print("no parcel")
    SetParcel()

#Set Arc Directory and StageParams if needed
root.stageParams = config["DEFAULT"].get("stageParamsLocation","")
if (not os.path.isdir(root.stageParams)):
    root.stageParams = ""
if (not os.path.exists(root.workspace + "/groundconfig.prc")):
    root.stageParams=""
    
#Get or Set root.stageParams
if (root.stageParams == ""):
    print("no arc")
    SetStageParams()


config.set("DEFAULT","parcelDir",root.parcelDir)
config.set("DEFAULT","arcDir",root.arcDir)
config.set("DEFAULT","stageParamsLocation",root.stageParams)
config.set("DEFAULT","workspace",root.workspace)
with open('config.ini', 'w+') as configfile:
    config.write(configfile)

root.stageName = ""
root.stageLocation = ""

root.steveTable={
    "Steve_Label":"Steve LVD Settings",
    "Steve_material":"soil",
    "Steve_origin_x":0,
    "Steve_origin_y":0,
    "Steve_cell_sensitivity":0,
    "Steve_line_offset":0,
    "Steve_cell_minilen_side":0,
    "Steve_cell_minilen_top":0,
    "Steve_cell_minilen_bottom":0
}
root.steveMaterials=[
"soil",
"wool",
"sand",
"ice",
]

root.collisions=[]
root.maxCollisionsTag="Canvas_Collisions To Show"
#root.maxCollisions=50
root.stageLimit=125

root.stageDefaults ={
"Camera_Label":"Camera Boundaries",
"Camera_Left":-170,
"Camera_Right":170,
"Camera_Top":130,
"Camera_Bottom":-80,
"Camera_CenterX":0,
"Camera_CenterY":0,
"Blast_Label":"Blastzone Boundaries",
"Blast_Left":-240,
"Blast_Right":240,
"Blast_Top":192,
"Blast_Bottom":-140,
"Stage_Label":"Stage Data",
"Stage_Radius":80,
"Stage_Top":47,
"Stage_Bottom":-40,
"Stage_FloorY":0,
"Stage_OriginX":0,
"Stage_OriginY":0,
"Canvas_Label":"Canvas Settings",
""+root.maxCollisionsTag:50
}

root.stageDataTable = root.stageDefaults.copy()
def ConvertSteveTag(data):
    data = (data.lower()).replace("steve_","Steve_")
    if ("top" in data):
        data = "Steve_cell_minilen_top"
    elif ("side" in data):
        data = "Steve_cell_minilen_side"
    elif ("bottom" in data):
        data = "Steve_cell_minilen_bottom"
    return data

def GetData(data):
    if ("Steve" in data):
        data = ConvertSteveTag(data)
        return root.steveTable[data]
    elif (data in root.stageDataTable):
        return root.stageDataTable[data]
    else:
        return
def SetData(data,value):
    if ("Steve" in data):
        data = ConvertSteveTag(data)
        root.steveTable[data] = value
    elif (data in root.stageDataTable):
        root.stageDataTable[data] = value
        if ("Camera" in data):
            root.stageDataTable["Camera_CenterX"] = (GetData("Camera_Left")+GetData("Camera_Right"))/2
            root.stageDataTable["Camera_CenterY"] = (GetData("Camera_Top")+GetData("Camera_Bottom"))/2
    else:
        print("Error: "+data+" key not found")

root.levelFile = ""
root.modParams = ""
root.popup = None
root.popupOptions = {}
root.FirstLoad=True
root.Loading=True

#Deprecated
def SetStageFromRoot():
    print("Open Stage from root:"+root.modDir)

    if (root.modDir==""):
        SetYaml(False)
        return
    SetStage(root.modDir+ "/stage/")

def SetStageFromLVD():
    stageKey="/stage/"
    normalKey="/normal/"
    #We need to find whatever is in between stageKey and normalKey
    root.stageLocation = root.levelFile[:root.levelFile.index(normalKey)]
    root.stageName = root.stageLocation[root.stageLocation.index(stageKey)+len(stageKey):]
    print("Stage:"+root.stageName)
    if (root.stageName == ""):
        messagebox.showerror(root.programName,"There is no valid stage within that stage folder!")
        return
    root.modParams = root.stageLocation+"/normal/param/"
    root.modDir = root.levelFile[:root.levelFile.index(stageKey)]
    print("Stage Loaded, stage params should be at "+root.modParams)

def SetStage(stageDir):
    print("Find stage at "+stageDir)
    root.stageName = None
    subfolders = [s.path for s in os.scandir(stageDir) if s.is_dir()]
    for dirname in list(subfolders):
        if (dirname != "common"):
            root.stageName = os.path.basename(dirname)
    if (root.stageName == None):
        messagebox.showerror(root.programName,"There is no valid stage within that stage folder!")
        return
        #root.destroy()
        #sys.exit("Not a stage folder")

def FinishedCreateYaml():
    #create yaml by copying our sample
    #root.levelFile = root.modParams+root.stageName+"_spec.yaml"
    shutil.copy(os.getcwd() + "/sample.yaml", root.levelFile)

    # Replace all tagged values
    with open(root.levelFile, 'r') as file :
        filedata = file.read()

    for option in root.popupOptions:
        filedata = filedata.replace(option, root.popupOptions[option].get())

    filedata = filedata.replace("RingL", "-"+root.popupOptions["StageRadius"].get())
    filedata = filedata.replace("RingR", root.popupOptions["StageRadius"].get())

    # Write to the copy
    with open(root.levelFile, 'w') as file:
        file.write(filedata)

    #Destroy popup, and return to main
    root.popup.destroy()
    root.deiconify()
    LoadYaml()

def ClosedCreateYaml():
    root.levelFile=""
    root.popup.destroy()
    root.deiconify()
    LoadYaml()

def CreateYaml():
    print(root.levelFile)
    if (root.levelFile==""):   
        messagebox.showinfo(root.programName,"Set directory to save yaml to")
        root.modParams = filedialog.askdirectory(title = "Select your yaml directory")
        if (root.modParams == ""):
            return
        root.levelFile = root.modParams
        SetStageFromLVD()
        print("Create Stage:"+root.stageName)
        root.levelFile=root.modParams+root.stageName+"_spec.yaml"

    root.popup = Toplevel()
    root.popup.title("Create Yaml")

    root.fr_Options = Frame(root.popup)
    root.fr_Options.pack(fill = BOTH,expand=1,anchor=N)
    root.popupOptions = {}
    stageOptions = {
    "Label1":"Camera Settings",
    "CameraLeft":root.stageDefaults["Camera_Left"],"CameraRight":root.stageDefaults["Camera_Right"],
    "CameraTop":root.stageDefaults["Camera_Top"],"CameraBottom":root.stageDefaults["Camera_Bottom"],
    "Label2":"Blastzone Settings",
    "BlastLeft":root.stageDefaults["Blast_Left"],"BlastRight":root.stageDefaults["Blast_Right"],
    "BlastTop":root.stageDefaults["Blast_Top"],"BlastBottom":root.stageDefaults["Blast_Bottom"],
    "Label3":"Stage Settings",
    "StageRadius":root.stageDefaults["Stage_Radius"],"StageFloorY":root.stageDefaults["Stage_FloorY"],
    "StageTop":root.stageDefaults["Stage_Top"],"StageBottom":root.stageDefaults["Stage_Bottom"]}
    for option in stageOptions:
        if ("Label" in option):
            optionFrame = Frame(root.fr_Options)
            optionFrame.pack(fill = X,expand=1)
            optionName = Label(optionFrame,text=stageOptions[option])
            optionName.pack(fill = BOTH)
            continue
        optionData = stageOptions[option]
        optionFrame = Frame(root.fr_Options)
        optionFrame.pack(fill = X,expand=1)
        optionName = Entry(optionFrame,width=15)
        optionName.insert(0,option)
        optionName.configure(state ='disabled')
        optionName.pack(side = LEFT, fill = BOTH,anchor=E)
        optionValue = Entry(optionFrame,width=15)
        optionValue.insert(0,optionData)
        optionValue.pack(side = RIGHT, fill = BOTH,expand=1)
        root.popupOptions.update({option:optionValue})

    button = Button(root.popup, text="Create Yaml", command=FinishedCreateYaml,width = 10).pack(side=BOTTOM)
    root.popup.protocol("WM_DELETE_WINDOW", ClosedCreateYaml)
    root.withdraw();

def LoadLastYaml():
    root.levelFile = config["DEFAULT"]["levelFile"]
    if (not os.path.exists(root.levelFile)):
        root.levelFile = ""
    else:
        SetStageFromLVD()
    Main()

def SetYaml(automatic=False):
    SetData(root.maxCollisionsTag,root.stageDefaults[root.maxCollisionsTag])

    originalYaml = root.levelFile
    root.levelFile=""
    #Attempt to find automatically first, if valid directory file exists
    if (automatic and os.path.isdir(root.modParams)):
        if (root.levelFile == ""):
            #Automatically comb through modParams to find the first yaml file
            paramfiles = [f for f in listdir(root.modParams) if os.path.exists(os.path.join(root.modParams, f))]
            root.yaml = {}
            for f in list(paramfiles):
                filename = os.path.splitext(os.path.basename(f))[0]
                extension = os.path.splitext(os.path.basename(f))[1]
                if (extension == ".yaml"):
                    #if (root.stageName in filename): #this checks if the filename contains the stage name, which might not always be the case
                    root.levelFile = root.modParams +f
                    break

    if (root.levelFile != ""):
        print(os.path.basename(root.levelFile)+" was automatically retrieved")
    elif (root.levelFile == "" or not automatic):
        #SetYaml manually. First select an lvd/yaml file
        #messagebox.showinfo(root.programName,"Select your stage collision file (usually found in stage/normal/params)")        
        filetypes = (
            ('All File Types', '*.yaml *lvd'),
            ('Yaml File', '*.yaml'),
            ('LVD File', '*lvd')
        )
        desiredFile = filedialog.askopenfilename(title = "Load Level File",filetypes=filetypes,initialdir = root.modParams)

        if (desiredFile == ""):
            print("No lvd selected")
            #enter manually if rejected, and no current file
            if (root.levelFile == "" and originalYaml==""):
                messagebox.showwarning(root.programName,"Let's manually create a yaml file then!")
                CreateYaml()
            #otherwise close window?
            else:
                root.levelFile=originalYaml
            return

        #If accidentally selected the Yaml version instead of the lvd verison, select yaml instead
        possibleYaml = desiredFile.replace(".lvd",".yaml")
        if (os.path.exists(possibleYaml) and ".lvd" in desiredFile):
            res = messagebox.askquestion(root.programName,"A .yaml version exists of "+os.path.basename(desiredFile)+". If you select the lvd, this yaml will be overwritten."+
                "\nSelect .lvd and overwrite its .yaml?")
            if res != 'yes':
                desiredFile=possibleYaml

        desiredFileName = os.path.basename(desiredFile)
        extension = os.path.splitext(desiredFileName)[1]

        #If it's a yaml file, continue to the main program
        if (extension == ".yaml"):
            root.levelFile = desiredFile
        #else yamlvd it
        elif (extension == ".lvd"):
            print("Use yamlvd")

            #Get or Set Yamlvd
            root.yamlvd = config["DEFAULT"]["yamlvd"]
            if (not os.path.exists(root.yamlvd)):
                root.yamlvd = ""
            if (root.yamlvd == ""):
                print("no yamlvd")
                SetYamlvd()
            config.set("DEFAULT","yamlvd",root.yamlvd)
            with open('config.ini', 'w+') as configfile:
                    config.write(configfile)

            #run yamlvd on the lvd file
            root.levelFile = desiredFile.replace(".lvd",".yaml")
            subcall = [root.yamlvd,desiredFile,root.levelFile]
            with open('output.txt', 'a+') as stdout_file:
                process_output = subprocess.run(subcall, stdout=stdout_file, stderr=stdout_file, text=True)
                print(process_output.__dict__)
            #if yamlvd doesn't work with this stage, enter values manually
            if (not os.path.exists(root.levelFile)):
                #enter manually
                messagebox.showwarning(root.programName,"Yamlvd not compatible with this stage! Let's create a yaml file!")
                CreateYaml()
                return
        LoadYaml()

def LoadYaml():
    root.Loading=True
    root.collisions=[]
    print("")
    print("Loaded New Yaml")
    if (root.levelFile != ""):
        SetStageFromLVD() 

    Main() 


def GetConfigFromYaml():
    toReturn = root.modDir + root.stageParamsFolderShortcut + r"groundconfig_"
    toReturn = toReturn+os.path.basename(root.levelFile).replace(".yaml",".prcxml")
    return toReturn

def ParseSteve(ParseFromWorkspace=True):
    if (root.stageName == ""):
        return
    tree = None
    treeRoot = None

    sourceGroundInfo = os.getcwd() + r"\groundconfig.prcxml"
    if (not os.path.exists(sourceGroundInfo)):
        messagebox.showerror(root.programName,"Source Groundconfig missing from this folder")
        return

    workingGroundInfo=""
    if (ParseFromWorkspace):
        workingGroundInfo = root.workspace+"/groundconfig_"+os.path.basename(root.levelFile).replace(".yaml",".prcxml")
        #if (not os.path.exists(workingGroundInfo)):
        #    messagebox.showerror(root.programName,"No data for "+os.path.basename(root.levelFile)+" found in workspace")
        #    return

    SetData("Steve_Side", 0)
    SetData("Steve_Top",0)
    SetData("Steve_Bottom", 0)

    if (ParseFromWorkspace):
        if (not os.path.exists(workingGroundInfo)):
            ParseFromWorkspace=False
        else:
            #Make sure the mod has our desired stage
            hasStage = False
            while hasStage == False:
                with open(workingGroundInfo, 'rb') as file:
                    parser = ET.XMLParser(encoding ='utf-8')
                    tree = ET.parse(file,parser)
                    treeRoot = tree.getroot()
                    for type_tag in treeRoot.findall('struct'):
                        nodeName = type_tag.get('hash')
                        if (nodeName == root.stageName):
                            hasStage=True
                break
            ParseFromWorkspace = hasStage
            print("Current mod's groundconfig excludes the desired stage, using source instead")

    root.TempGroundInfo = os.getcwd() + r"\tempconfig.prcxml"
    f = open(root.TempGroundInfo, "w")
    f.close()

    GroundInfo = workingGroundInfo if ParseFromWorkspace else sourceGroundInfo

    print("Parsing Steve Data...")
    #Parse Steve data from main groundconfig file and place it in a temporary file
    with open(GroundInfo, 'rb') as file:
        parser = ET.XMLParser(encoding ='utf-8')
        tree = ET.parse(file,parser)
        treeRoot = tree.getroot()

        #remove cell_size
        for type_tag in treeRoot.findall('float'):
            treeRoot.remove(type_tag)
        #remove material_tabel
        for type_tag in treeRoot.findall('list'):
            treeRoot.remove(type_tag)
        #remove everything that isn't this stage
        for type_tag in treeRoot.findall('struct'):
            nodeName = type_tag.get('hash')
            if (nodeName != root.stageName):
                treeRoot.remove(type_tag)
            else:
                for child in type_tag:
                    childName = "Steve_"+child.get("hash")
                    if (childName in list(root.steveTable.keys())):
                        print(childName+":"+child.text)
                        if (childName!="Steve_material"):
                            root.steveTable.update({childName:float(child.text)})
                        else:
                            root.steveTable.update({childName:child.text})
        tree.write(root.TempGroundInfo)
    print("")


def SaveGroundInfoChanges():
    tree = None
    treeRoot = None

    #Write our changes to TempGroundInfo
    with open(root.TempGroundInfo, 'rb') as file:
        parser = ET.XMLParser(encoding ='utf-8')
        tree = ET.parse(file,parser)
        treeRoot = tree.getroot()

        for type_tag in treeRoot.findall('struct'):
            nodeName = type_tag.get('hash')
            if (nodeName != root.stageName):
                treeRoot.remove(type_tag)
            else:
                for child in type_tag:
                    childName = "Steve_"+child.get("hash")
                    if (childName in list(root.steveTable.keys())):
                        value = GetData(childName)
                        print("Write:"+childName+":"+str(value))
                        child.text = str(value)
        tree.write(root.TempGroundInfo)

    targetFile = GetConfigFromYaml()
    targetFile = root.workspace + "/"+os.path.basename(targetFile)
    #Copy the temp prcxml to our workspace
    shutil.copy(root.TempGroundInfo,targetFile)
    root.UnsavedChanges=False
    UpdateTitleAuto()

#def ReadPrcxml(file):

def PatchWorkspace():
    workspacePrcxml = root.workspace+"/groundconfig.prcxml"
    f = open(workspacePrcxml, "w")
    f.close()

    mainTree = None
    mainTreeRoot = None

    patchCreated=False
    #For each PRCXML in the workspace (that isnt groundconfig), add it to the mainTree
    with open(workspacePrcxml, 'rb') as file:
        mainParser = ET.XMLParser(encoding ='utf-8')
        mainTreeRoot = ET.Element("struct")
        mainTree = ET.ElementTree(mainTreeRoot)

        prcxmls = [f.path for f in os.scandir(root.workspace) if f.is_file()]
        stages=[]
        for file in list(prcxmls):
            fileName = os.path.basename(file)
            fileName = os.path.basename(os.path.splitext(file)[0])
            fileExt = os.path.splitext(file)[1]
            if (fileName != "groundconfig" and fileExt == ".prcxml"):
                with open(file, 'rb') as prcxml:
                    parser = ET.XMLParser(encoding ='utf-8')
                    tree = ET.parse(prcxml,parser)
                    treeRoot = tree.getroot()
                    if (len(treeRoot)>0):
                        patchCreated=True
                        stageName = treeRoot[0].get('hash')
                        print(stageName)
                        isNewEntry = True
                        if (stageName in stages):
                            messagebox.showwarning(root.programName,"Multiple files in workspace use stage '"+stageName+"'!"+
                                "\nValues will be overwritten, it is recommended that each stage has only one file in a workspace!")
                            for type_tag in mainTreeRoot.findall("struct"):
                                nodeName = type_tag.get('hash')
                                if (nodeName==stageName):
                                    mainTreeRoot.remove(type_tag)
                        mainTreeRoot.append(treeRoot[0])
                        stages.append(stageName)
        #Write XML
        mainTree.write(workspacePrcxml, encoding="utf-8", xml_declaration=True) 

    if (not patchCreated):
        messagebox.showwarning(root.programName,"No files to patch")
        return

    parcel = root.parcelDir + r"/parcel.exe"

    #Patch the source file with our workspacePrcxml, and create a clone as our workspaces' prc
    sourcePrc = root.stageParams + "groundconfig.prc"
    workspacePrc = workspacePrcxml.replace(".prcxml",".prc")
    subcall = [parcel,"patch",sourcePrc,workspacePrcxml,workspacePrc]
    with open('output.txt', 'a+') as stdout_file:
        process_output = subprocess.run(subcall, stdout=stdout_file, stderr=stdout_file, text=True)
        print(process_output.__dict__)

    print("Prc created!")

    #Create Prcx for mod
    targetFile = workspacePrcxml.replace(".prcxml",".prcx")

    subcall = [parcel,"diff",sourcePrc,workspacePrc,targetFile]
    with open('output.txt', 'a+') as stdout_file:
        process_output = subprocess.run(subcall, stdout=stdout_file, stderr=stdout_file, text=True)
        print(process_output.__dict__)

    print("Prcx created!")

    messagebox.showinfo(root.programName,"Workspace patch file and prc created!")
    webbrowser.open(root.workspace)


def exportGroundInfo():
    tempPrc = os.getcwd() +"/temp.prc"
    sourcePrc = root.stageParams + "groundconfig.prc"
    parcel = root.parcelDir + r"/parcel.exe"

    if (not os.path.exists(sourcePrc)):
        messagebox.showerror(root.programName,"Cannot export without ArcExplorer's groundconfig.prc")
        return
    if (not os.path.exists(parcel)):
        messagebox.showerror(root.programName,"Cannot export without Parcel")
        return

    #Changes must be saved before exporting
    SaveGroundInfoChanges()

    #Patch the source file with our edited values, and create a clone as TempPRC

    subcall = [parcel,"patch",sourcePrc,root.TempGroundInfo,tempPrc]
    with open('output.txt', 'a+') as stdout_file:
        process_output = subprocess.run(subcall, stdout=stdout_file, stderr=stdout_file, text=True)
        print(process_output.__dict__)
    print("Temp prc created!")

    #Patch our workspace's prc, as well
    workingPrc = root.workspace + "/groundconfig.prc"
    if (os.path.exists(workingPrc)):
        subcall = [parcel,"patch",workingPrc,root.TempGroundInfo,workingPrc]
        with open('output.txt', 'a+') as stdout_file:
            process_output = subprocess.run(subcall, stdout=stdout_file, stderr=stdout_file, text=True)
            print(process_output.__dict__)

        print("Working prc patched!")
        #Run parcel with the original and the patch to receive a prcx
    else:
        messagebox.showwarning(root.programName,"groundconfig.prc missing from LvdSpec")

    #Create Prcx for mod
    targetLocation = root.modDir + root.stageParamsFolderShortcut
    if (not os.path.exists(targetLocation)):
        os.makedirs(targetLocation)
    targetFile = targetLocation+"groundconfig.prcx"

    subcall = [parcel,"diff",sourcePrc,tempPrc,targetFile.replace(".prcxml",".prcx")]
    with open('output.txt', 'a+') as stdout_file:
        process_output = subprocess.run(subcall, stdout=stdout_file, stderr=stdout_file, text=True)
        print(process_output.__dict__)

    print("Prcx created!")

    #Copy the temp prcxml to the destination
    #shutil.copy(root.TempGroundInfo,targetFile)

    #Final part: remove temp and navigate to new folder
    os.remove(tempPrc)
    messagebox.showinfo(root.programName,"Exported steve parameters as "+os.path.basename(targetFile)+"!"
        "\nMake sure you rename the file to 'groundconfig' in your mod file"
        "\n"
        "\nLVDSpec's groundconfig.prc has also been updated!")
    webbrowser.open(targetLocation)


def OpenReadMe():
    webbrowser.open('https://github.com/CSharpM7/LVDSpec')
def OpenWiki():
    webbrowser.open('https://github.com/CSharpM7/LVDSpec/wiki')

root.string_vars = {}

def OnSteveSliderUpdate(variable):
    if (root.Loading):
        return
    value = root.stageData[variable].get()
    value=float(value)
    print("Updated "+variable+" with "+str(value))
    root.steveTable.update({variable:value})
    #Until we know what sensitivity and offset do, we can't update the steve block
    #DrawSteveBlock()

def OnOriginXSliderUpdate(event):
    variable = "Steve_origin_x"
    OnSteveSliderUpdate(variable)
def OnOriginYSliderUpdate(event):
    variable = "Steve_origin_y"
    OnSteveSliderUpdate(variable)
def OnLineSliderUpdate(event):
    variable = "Steve_line_offset"
    OnSteveSliderUpdate(variable)
def OnSensitivitySliderUpdate(event):
    variable = "Steve_cell_sensitivity"
    OnSteveSliderUpdate(variable)

def OnSettingUpdated(variable):
    #Get Value, only take #s,- and .
    value = root.string_vars[variable].get()
    value,isValidValue = GetStringAsNumber(value)
    if (not isValidValue): return
    value=float(value)
      
    #Convert Collisions to int 
    if (variable==root.maxCollisionsTag and value != ""):
        value=int(value)
    #Clamp Radius
    elif ("Radius" in variable):
        value=min(value,root.stageLimit)
    #Clamp Steve Origins
    elif ("Steve_origin" in variable):
        value=clamp(value,-10,10)

    SetData(variable,value)
    #print("Updated "+variable+" with "+str(value))

    if ("Canvas" in variable):
        DrawCollisions()
    else:
        if ("Stage" in variable):
            DrawBoundaries()
        elif ("Steve" in variable):
            if (not root.UnsavedChanges):
                root.UnsavedChanges=True
                UpdateTitleAuto()
            DrawSteveBlock()
        DrawGrid()

def OnSteveSettingUpdated(*args):
    if (root.Loading):
        return
    variable = "Steve_"+args[0]
    OnSettingUpdated(variable)

def OnStageSettingUpdated(*args):
    if (root.Loading):
        return
    variable = "Stage_"+args[0]
    OnSettingUpdated(variable)

def OnCanvasSettingUpdated(*args):
    if (root.Loading):
        return
    variable = "Canvas_"+args[0]
    OnSettingUpdated(variable)


def LoadLevel():
    if (root.UnsavedChanges):
        res = messagebox.askquestion(root.programName,"There are unsaved changes! Are you sure you want to load a new file?"
            ,icon = "warning")
        if res != 'yes':
            return
    SetYaml()

root.canvasWidth = 576
root.canvasHeight = 480 
#This should really only run once, maybe I should split this up but idk
def CreateCanvas():
    #Define window stuff
    root.geometry("1080x512")
    root.deiconify()
    root.mainFrame = Frame(root)
    root.mainFrame.pack(fill = X,expand=1)
    root.my_canvas = Canvas(root.mainFrame,width=root.canvasWidth,height=root.canvasHeight,bg="white")
    root.my_canvas.pack(padx=20,pady=20,side=LEFT)
    #Rectangle variables for later
    root.steveArea = root.my_canvas.create_rectangle(-10,-10,-10,-10,fill = "lime green",tag="steve")
    root.cameraArea = root.my_canvas.create_rectangle(-10,-10,-10,-10,outline = "blue",tag="camera")
    root.blastArea = root.my_canvas.create_rectangle(-10,-10,-10,-10,outline = "red",tag = "blast")

    #File menu
    root.menubar = Menu(root)
    root.filemenu = Menu(root.menubar, tearoff=0)
    root.filemenu.add_command(label="Load Stage Collision File", command=LoadLevel)
    root.filemenu.add_command(label="Save To Workspace", command=SaveGroundInfoChanges)
    root.filemenu.add_separator()
    root.filemenu.add_command(label="Export Patch File To Mod", command=exportGroundInfo)
    root.filemenu.add_command(label="Create Workspace Patch", command=PatchWorkspace)
    root.filemenu.add_separator()
    root.filemenu.add_command(label="Exit", command=quit)
    root.menubar.add_cascade(label="File", menu=root.filemenu)

    root.settingsmenu = Menu(root.menubar, tearoff=0)
    root.settingsmenu.add_command(label="Set Workspace", command=SetWorkspace)
    root.menubar.add_cascade(label="Settings", menu=root.settingsmenu)

    root.helpmenu = Menu(root.menubar, tearoff=0)
    root.helpmenu.add_command(label="About", command=OpenReadMe)
    root.helpmenu.add_command(label="Wiki", command=OpenWiki)
    root.menubar.add_cascade(label="Help", menu=root.helpmenu)
    root.config(menu=root.menubar)

    #Settings displayed on the side,
    root.fr_Settings = Frame(root.mainFrame)
    root.fr_Settings.pack(pady=20,expand=1,fill=BOTH,side=RIGHT)
    root.fr_SteveSettings = Frame(root.fr_Settings)
    root.fr_SteveSettings.pack(padx=10,side=LEFT,anchor=N)
    root.fr_StageSettings = Frame(root.fr_Settings)
    root.fr_StageSettings.pack(padx=10,side=LEFT,anchor=N)

    root.stageData = {}
    dataTable = {}
    dataTable.update(root.steveTable)
    dataTable.update(root.stageDataTable)
    for data in dataTable:
        frame = root.fr_StageSettings
        if ("Steve" in data):
            frame = root.fr_SteveSettings
        #For labels, don't use Entries
        if ("Label" in data):
            dataFrame = Frame(frame)
            dataFrame.pack(fill = X,expand=1)
            dataName = Label(dataFrame,text=dataTable[data])
            dataName.pack(fill = BOTH)
            continue

        dataText=re.sub(r'[^a-zA-Z _]', '', data)
        dataText=dataText[dataText.index("_")+1:]
        dataDefault = str(dataTable[data])

        dataFrame = Frame(frame)
        dataFrame.pack(fill = X,expand=1)

        dataName = Entry(dataFrame)
        dataName.insert(0,dataText)
        dataName.configure(state ='disabled')
        dataName.pack(side = LEFT, fill = BOTH,anchor=E)
        dataEntry=None
        #For Steve Entries, trace any updates
        if ("Steve" in data or "Stage" in data or "Canvas" in data):
            #Sensitivity is a slider
            if ("sensitivity" in data):
                dataEntry = Scale(dataFrame, from_=0, to=1,orient=HORIZONTAL,resolution=0.01)
                dataEntry.bind("<ButtonRelease-1>",OnSensitivitySliderUpdate)
                dataEntry.set(dataDefault)
            elif ("line" in data):
                dataEntry = Scale(dataFrame, from_=0, to=10,orient=HORIZONTAL,resolution=0.01)
                dataEntry.bind("<ButtonRelease-1>",OnLineSliderUpdate)
                dataEntry.set(dataDefault)
            #Origin is now using textEntry
            elif ("Xorigin" in data):
                dataEntry = Scale(dataFrame, from_=-10, to=10,orient=HORIZONTAL,resolution=0.01)
                dataEntry.set(dataDefault)
                if ("_x" in data):
                    dataEntry.bind("<ButtonRelease-1>",OnOriginXSliderUpdate)
                elif ("_y" in data):
                    dataEntry.bind("<ButtonRelease-1>",OnOriginYSliderUpdate)
            else:
                root.string_vars.update({data:StringVar(name=dataText)})
                var = root.string_vars[data]
                if ("Steve" in data):
                    var.trace_add("write",OnSteveSettingUpdated)
                elif ("Stage" in data):
                    var.trace_add("write",OnStageSettingUpdated)
                else:
                    var.trace_add("write",OnCanvasSettingUpdated)

                dataEntry = Entry(dataFrame,textvariable=var)
                dataEntry.insert(0,dataDefault)

                #Material is uneditable
                if ("material" in data):
                    dataEntry.configure(state ='disabled')
        #Disable non-editable categories
        else:
            dataEntry = Entry(dataFrame)
            dataEntry.insert(0,dataDefault)
            dataEntry.configure(state ='disabled')
        dataEntry.pack(side = RIGHT, fill = BOTH,expand=1)
        root.stageData.update({data:dataEntry})

    #Default Button
    button = Button(root.fr_SteveSettings, text="Reset Values To Default", command=OnDefault)
    button.pack(side = TOP, fill = BOTH,expand=1,pady=8,padx=4)
    #Workspace Button
    button = Button(root.fr_SteveSettings, text="Load Values From Workspace", command=OnWorkspace)
    button.pack(side = TOP, fill = BOTH,expand=1,pady=8,padx=4)
    #Wizard Button
    button = Button(root.fr_SteveSettings, text="Wizard", command=OnWizard,width=10)
    button.pack(side = TOP,expand=1,pady=8)
    #ReParse Button
    button = Button(root.fr_StageSettings, text="Reparse Stage Data", command=OnReParse)
    button.pack(side = RIGHT, fill = BOTH,expand=1,pady=8,padx=4)

def OnReParse():
    ParseYaml()
    RefreshValues()
    RefreshCanvas()

def OnDefault():
    res = messagebox.askquestion("LVD Wizard: "+os.path.basename(root.levelFile), "Reset Steve parameters to their original values?")
    if res != 'yes':
        return
    ParseSteve()
    RefreshValues()
    RefreshCanvas()

def OnWorkspace():
    workingGroundInfo = root.workspace+"/groundconfig_"+os.path.basename(root.levelFile).replace(".yaml",".prcxml")
    if (not os.path.exists(workingGroundInfo)):
        messagebox.showerror(root.programName,"No data for "+os.path.basename(root.levelFile)+" found in workspace")
        return

    res = messagebox.askquestion("LVD Wizard: "+os.path.basename(root.levelFile), "Load Steve parameters from your workspace?")
    if res != 'yes':
        return
    ParseSteve(True)
    RefreshValues()
    RefreshCanvas()

def OnWizard():
    res = messagebox.askquestion("LVD Wizard: "+os.path.basename(root.levelFile), "Make sure you have all these variables set in Stage Data for this to work!"
        "\n"
        "\nRadius (Radius of the main ring)"
        "\nTop (Y Position of highest platform, could be a spawn point's y)"
        "\nBottom (Y Position of lowest point on the main ring)"
        "\nFloorY (Y Position of baseline on the main ring, should be a spawn point's y)"
        "\nOrigin (A multiple of 50 that is as close to 0,0 as possible. For stages that have been shifted up/left, this could be 0,200 for a highup stage, or 100,0 for a stage that's far to the right)"
        "\n"
        "\nReady to start Wizard?")
    if res != 'yes':
        return
    #BF (plankable)
    #Side: Steve40,Cam170
    #Bottom: Steve30,Cam-80
    #Top: Steve60,Cam130,Stage47
    #BottomStage: 40
    #Radius: 80 (90 or 2.125)

    #FD (plankable)
    #Side: Steve50,Cam180
    #Bottom: Steve10,Cam-60
    #Top: Steve70,Cam130,Stage0
    #BottomStage: 40
    #Radius: 80 (100 or 2.25)

    #Kalos (wall)
    #Side: Steve35,Cam165
    #Bottom: Steve10,Cam-60
    #Top: Steve70,Cam130,Stage30
    #BottomStage: -inf
    #Radius: 80 (85 or 2.062)

    #T&C (good)
    #Side: Steve28,Cam160
    #Bottom: Steve40,Cam-75
    #BottomStage: -23.5
    #Radius: 83 (77 or 1.927)

    #Buffer between TopPlat's position and the highest block, and various other Y parameters
    BufferY=20

    stageHeight = abs(GetData("Stage_FloorY")-GetData("Stage_Bottom"))
    isWall= (GetData("Stage_Bottom")<GetData("Camera_Bottom")+5)
    if (isWall):
        stageHeight= abs(GetData("Stage_FloorY")-GetData("Camera_Bottom"))
    print("Wizard: Stage is using wall:"+str(isWall))


    #Origin should do something with CameraCenter
    cameraCenter = GetData("Camera_CenterX")
    #I think originX is also 10-(Radius mod 10)
    desiredOriginX= cameraCenter + (10-(GetData("Stage_Radius") % 10))
    if (abs(desiredOriginX)>=10):
        desiredOriginX=0
    #desiredOriginX = cameraCenter%10
    desiredOriginY=GetData("Stage_FloorY") % 10

    #SteveBottom should be the StageFloor-(3 blocks)
    target=GetData("Stage_FloorY")-30
    if (isWall):
        target=target-10
    desiredBottom = abs(GetData("Camera_Bottom")-target)
    #If for some reason the bottom is lower than the bottom of the camera, set it to 0
    desiredBottom=max(math.floor(desiredBottom),0)

    #SteveSide seems to be the middle of Camera and the rightmost part of the stage (found by combining radius and origin)
    shiftedCenter=GetData("Stage_Radius")+GetData("Stage_OriginX")
    desiredSide = ((GetData("Camera_Right")-shiftedCenter)/2)-GetData("Stage_OriginX")
    desiredSide=math.floor(desiredSide)

    #For TopFromBase, we'll take the median of CameraTop and the base of the stage
    TopFromBase=math.floor((GetData("Camera_Top")-GetData("Stage_FloorY"))/2)
    #For TopPlat, we'll take Stage_Top to the nearest 10, offset it by originY
    TopPlat = (math.ceil(GetData("Stage_Top")/10)*10)+desiredOriginY
    TopFromPlat=math.floor((GetData("Camera_Top")-TopPlat-BufferY))
    print("Wizard: TopFromBase:"+str(TopFromBase)+"; FromPlat:"+str(TopFromPlat))
    #Pick whichever is the smallest amount
    desiredTop=min(TopFromBase,TopFromPlat)


    SetData("Steve_Top",desiredTop)
    SetData("Steve_Side",desiredSide)
    SetData("Steve_Bottom",desiredBottom)
    SetData("Steve_origin_x",desiredOriginX)
    SetData("Steve_origin_Y",desiredOriginY)
    print("Wizard finished!")
    RefreshValues()
    messagebox.showinfo(root.programName,"Steve parameters automatically set!")


#Load info from yaml into our canvas
def ParseYaml():
    if (root.levelFile==""): return

    print("Parsing yaml:"+root.levelFile)
    with open(root.levelFile, "r") as stream:
        try:
            root.yaml = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            messagebox.showerror(root.programName+":"+os.path.basename(root.levelFile),"FATAL"+exc)
            config.set("DEFAULT","levelFile","")
            with open('config.ini', 'w+') as configfile:
                config.write(configfile)

            root.destroy()
            sys.exit("Yaml exploded")

    try:
        stageDataTableUpdates = {}
        stageDataTableUpdates.update(root.stageDefaults)
        root.collisions=[]
        spawns=[]
        for i in root.yaml:
            #print(i)
            #Get Camera Info
            if ("camera" in i and (not "shrunk" in i)):
                SetData("Camera_Left",float(root.yaml[i][0]["left"]))
                SetData("Camera_Right",float(root.yaml[i][0]["right"]))
                SetData("Camera_Top",float(root.yaml[i][0]["top"]))
                SetData("Camera_Bottom",float(root.yaml[i][0]["bottom"]))
            #get boundary Info
            elif ("blast" in i and (not "shrunk" in i)):
                SetData("Blast_Left",float(root.yaml[i][0]["left"]))
                SetData("Blast_Right",float(root.yaml[i][0]["right"]))
                SetData("Blast_Top",float(root.yaml[i][0]["top"]))
                SetData("Blast_Bottom",float(root.yaml[i][0]["bottom"]))
            #get collision Info
            elif (i=="collisions"):
                for c in root.yaml[i]:
                    #Some yamls have verticies instead of verts
                    vertices = "verts"
                    if (not vertices in c):
                        vertices="vertices"
                    root.collisions.append(c[vertices])
            #get spawn
            elif (i=="spawns"):
                for s in root.yaml[i]:
                    pos_y = s["pos"]["y"]
                    spawns.append(float(pos_y))

        print("Camera / Blast")
        #Parse stage data
        largestX=0
        cameraLeftValue=GetData("Camera_Left")
        cameraRightValue=GetData("Camera_Right")
        cameraBottomValue=GetData("Camera_Bottom")
        cameraTopValue=GetData("Camera_Top")
        originX=GetData("Camera_CenterX")
        originY=GetData("Camera_CenterY")
        highestSpawn=-1000 if (len(spawns)>0) else originY
        lowestSpawn=1000 if (len(spawns)>0) else originY
        lowestY=1000
        highestY=-1000
        for s in spawns:
            if (s>highestSpawn):
                highestSpawn=s
            if (s<lowestSpawn):
                lowestSpawn=s

        print("Spawn")
        maxCol = GetData(root.maxCollisionsTag)
        currentCol = 0
        for c in root.collisions:
            for vert in range(len(c)-1):
                x1=float(c[vert]["x"])
                y1=float(c[vert]["y"])
                #Make sure largestX is in between camera boundaries
                if (x1>largestX and cameraLeftValue<x1 and x1<cameraRightValue):
                    largestX=x1
                #Make sure lowestY is in between blast boundaries
                if (y1<lowestY and cameraBottomValue<y1):
                    lowestY=y1
                #Make sure highestY is in between camera boundaries
                if (y1>highestY and cameraTopValue>y1):
                    highestY=y1

            #If next collision is greater than maxVisible, then break
            currentCol=currentCol+1
            if (currentCol>=maxCol):
                break
        SetData("Stage_Radius",min(largestX,root.stageLimit))
        SetData("Stage_Top",highestY)
        SetData("Stage_FloorY", lowestSpawn)
        SetData("Stage_OriginX", math.floor(originX/50)*50)
        SetData("Stage_OriginY", math.floor(originY/50)*50)
        SetData("Stage_Bottom",lowestY)
    except Exception as exc:
        messagebox.showerror(root.programName+":"+os.path.basename(root.levelFile),"FATAL: "+str(exc))
        config.set("DEFAULT","levelFile","")
        with open('config.ini', 'w+') as configfile:
            config.write(configfile)

        root.destroy()
        sys.exit("Yaml exploded")

root.my_canvas = None

def GetAdjustedCoordinates(x=0,y=0):
    #Center Of Canvas
    xC = root.canvasWidth/2
    yC = root.canvasHeight/2
    #Offset, center of camera boundaries
    xO = GetData("Camera_CenterX")
    yO = GetData("Camera_CenterY")
    #Coordinates
    if (x!=None):
        x=x+xC+xO
    if (y!=None):
        y=(-y)+yC+yO

    #I really should learn how to return dynamic variable lengths
    if (x==None):
        return y
    elif (y==None):
        return x
    else:
        return x,y


def DrawSteveBlock():
    if (root.stageName == ""):
        root.my_canvas.coords(root.steveArea,-10,-10,-10,-10)
        return

    side=GetData("Steve_Side")
    top=GetData("Steve_Top")
    bottom=GetData("Steve_Bottom")
    xC = root.canvasWidth/2
    yC = root.canvasHeight/2
    x1 = GetData("Camera_Left")+side
    x2 = GetData("Camera_Right")-side
    y1 = GetData("Camera_Top")-top
    y2 = GetData("Camera_Bottom")+bottom
    camCX = GetData("Camera_CenterX")
    camCY = GetData("Camera_CenterY")
    if (x1>camCX):
        x1=camCX
    if(x2<camCX):
        x2=camCX
    if (y1<camCY):
        y1=camCY
    if(y2>camCY):
        y2=camCY
    x1,y1 = GetAdjustedCoordinates(x1,y1)
    x2,y2 = GetAdjustedCoordinates(x2,y2)
    root.my_canvas.coords(root.steveArea,x1,y1,x2,y2)

def DrawGrid():
    #Create Grid for Steveblock
    root.my_canvas.delete('grid_line')

    xO=float(GetData("Steve_origin_x"))+GetData("Stage_OriginX")
    yO=float(GetData("Steve_origin_y"))+GetData("Stage_OriginY")
    xO,yO = GetAdjustedCoordinates(xO,yO)
    radius=GetData("Stage_Radius")
    maxX=int(radius)+10
    minY=-20
    maxY=30
    #Vertical Lines
    for i in range(-maxX,maxX+1,10):
        root.my_canvas.create_line([(xO+i, yO-maxY), (xO+i, yO-minY)], tag='grid_line',fill='dark green')
    #Horizontal Lines
    for i in range(minY,maxY+1,10):
        root.my_canvas.create_line([(xO-maxX, yO-i), (xO+maxX, yO-i)], tag='grid_line',fill='dark green')


def DrawBoundaries():
    x1,y1 = GetAdjustedCoordinates(GetData("Camera_Left"),GetData("Camera_Top"))
    x2,y2 = GetAdjustedCoordinates(GetData("Camera_Right"),GetData("Camera_Bottom"))
    root.my_canvas.coords(root.cameraArea,x1,y1,x2,y2)

    #Draw guidelines for stuff
    root.my_canvas.delete('guide_line')

    stageBottom = GetData("Stage_Bottom")
    empty,stageBottom = GetAdjustedCoordinates(0,stageBottom)
    root.my_canvas.create_line([(x1, stageBottom), (x2,stageBottom)], tag='guide_line',fill='grey')

    stageFloor = GetData("Stage_FloorY")
    empty,stageFloor = GetAdjustedCoordinates(0,stageFloor)
    root.my_canvas.create_line([(x1, stageFloor), (x2,stageFloor)], tag='guide_line',fill='grey')

    stageTop = GetData("Stage_Top")
    empty,stageTop = GetAdjustedCoordinates(0,stageTop)
    root.my_canvas.create_line([(x1, stageTop), (x2,stageTop)], tag='guide_line',fill='grey')

    xO=float(GetData("Stage_OriginX"))
    yO=float(GetData("Stage_OriginY"))
    xO,yO = GetAdjustedCoordinates(xO,yO)
    radius=GetData("Stage_Radius")
    root.my_canvas.create_line([(xO-radius, stageTop), (xO-radius, stageFloor)], tag='guide_line',fill='grey',width=2)
    root.my_canvas.create_line([(xO+radius, stageTop), (xO+radius, stageFloor)], tag='guide_line',fill='grey',width=2)

    x1,y1 = GetAdjustedCoordinates(GetData("Blast_Left"),GetData("Blast_Top"))
    x2,y2 = GetAdjustedCoordinates(GetData("Blast_Right"),GetData("Blast_Bottom"))
    root.my_canvas.coords(root.blastArea,x1,y1,x2,y2)

def DrawCollisions():
    root.my_canvas.delete("collision")
    for c in range(min(len(root.collisions),GetData(root.maxCollisionsTag))):
        col = root.collisions[c]
        for vert in range(len(col)-1):
            x1=float(col[vert]["x"])
            y1=float(col[vert]["y"])
            x2=float(col[vert+1]["x"])
            y2=float(col[vert+1]["y"])
            x1,y1 = GetAdjustedCoordinates(x1,y1)
            x2,y2 = GetAdjustedCoordinates(x2,y2)
            root.my_canvas.create_line(x1,y1,x2,y2, fill = "black",width=2,tags="collision")

#If yaml file is reloaded, then you should call this
def RefreshCanvas():
    DrawSteveBlock()
    DrawGrid()
    DrawBoundaries()
    DrawCollisions()

def RefreshValues():
    print("Refreshing for "+root.stageName)
    disableSteve = "disable" if (root.stageLocation=="") else "normal"
    for data in root.stageData:
        entry = root.stageData[data]
        value =str(GetData(data))
        if ("Steve" in data):
            entry.configure(state = "normal")
            if ("sensitivity" in data or "line" in data or "Xorigin" in data):
                entry.set(value)
            else:
                entry.delete(0,END)
                if (root.stageName==""):
                    entry.insert(0,"?")
                else:
                    entry.insert(0,value)

            if ("material" in data): 
                entry.configure(state = "disable")
            else:
                entry.configure(state = disableSteve)
        else:
            entry.configure(state = "normal")
            entry.delete(0,END)
            entry.insert(0,value)
            if ("Canvas" in data or "Stage" in data):
                entry.configure(state = disableSteve)
            else:
                entry.configure(state = "disable")
    root.filemenu.entryconfig("Export Patch File To Mod", state=disableSteve)

def Main():
    print("Running main: "+root.stageName)
    if (root.stageName!="" and os.path.exists(root.levelFile)):
        UpdateTitleAuto()
    else:
        UpdateTitle()

    ParseSteve()
    ParseYaml()
    if (root.FirstLoad):
        CreateCanvas()
    else:
        RefreshValues()
    RefreshCanvas()
    root.FirstLoad=False
    root.Loading=False
    config.set("DEFAULT","levelFile",root.levelFile)
    with open('config.ini', 'w+') as configfile:
        config.write(configfile)

def quit():
    if (root.UnsavedChanges):
        res = messagebox.askquestion(root.programName,"There are unsaved changes! Are you sure you want to exit?"
            ,icon = "warning")
        if res != 'yes':
            return
    root.withdraw()
    sys.exit("user exited")

LoadLastYaml()
root.protocol("WM_DELETE_WINDOW", quit)
root.mainloop()
