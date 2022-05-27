# A simple Python script for converting opentype unicode-based
# Tamil characters to glyph format suitable for pasting in
# Affinity programs. You will have to reformat all the
# text in Affinity after pasting the clipboard and toggling
# to unicode. The app converts the Tamil unicode text to
# a string of glyph data that can be displayed inside
# Affinity apps. This works only for certain unicode-based open
# type fonts. The script reads the .ttf file, extracts the cmap and
# GSUB lookup tables and saves them in a temporary .xml file
# for use. If the opentype .ttf font file contains all the
# necessary glyphs for Tamil and if they all are also indexed in
# GSUB lookup tables, this Python program script will work!
#
# Usage: select and copy-paste true-type Tamil text in the upper window,
# press convert, press copy to copy converted format to clipboard
# press clear to clear both screens and the clipboard.
#
# Easiest way to copy the converted data is: open a new Text box
# in Affinity, press 'cmd v' to paste inside, 'cmd a' to select all,
# ctrl u to toggle to unicode, and then change font to the
# correct one.
#
# known problems: only level 1 substitution is ready and so
# it does not display some sanskrit characters like sri or ksha.
# Also char 'vi' in Latha font does not display correctly in Affinity.
#
# Note that copied text inside Affinity is not font
# characters, but glyph characters. So, you won't be able
# to change the font family. But you can resize the characters
# and any minor editing can be done using the glyph browser.
# Only Tamil and English characters are allowed. If you have
# other non-unicode font texts, you will have to convert and
# add them separately. Non-Tamil unicode text is passed through
# the program without conversion. All the formatting in the
# original text is also lost during clip and paste. So, you
# will have to reformat the text after pasting in Affinity.
# Some unicode-based opentype may not display correctly if
# they do not have all the glyph encoded in the GSUB list.
# Fonts like Vijaya, Akshar, TAU-encoded Tamil fonts, and many
# more work well.
#
# In Latha font, chars like 'vi' does not display correctly
# since it depends on GPOS data, and not GSUB. The glyph for this
# character 'vi is not inside .ttf file, and it has to be rendered
# using GPOS table by the Affinity app. It does so somewhat imperfectly,
# but otherwise it's fine.
#
# For other Indic languages, you will have to change some of the data
# inside the section below in this program. Tested up to 20-page
# MS Word Akshar or Vijaya font documents. Google Tamil fonts
# do not work, since they do not depend entirely on psts substitution
# rules in the GSUB table. They use more open-type features. Good luck!
#
# Chakravathy Mathiazhagan, IIT Madras.
#

# update 26 May 2022 -- added support for .ttc font collection files
# fixed a bug that happens when both taml and tml2 versions are present
# update 27 May 2022 -- added checking for GSUB table in font file

from tkinter import *
import sys
import clipboard
import tkinter.font as font
from fontTools.ttLib import TTFont
import xml.etree.ElementTree as ET

# check for available fonts
# if sys.version_info.major == 3:
#    import tkinter as tk, tkinter.font as tk_font
# else:
#    import Tkinter as tk, tkFont as tk_font

finalDisp = ""  # global final display return value

# enter the language .ttf or .ttc font file below!
# strip and save a temp xml file with only GSUB and cmap tables for the font

font2 = TTFont("akshar.ttf", fontNumber=0)
font2.saveXML("temp.xml", tables=["GSUB", "cmap"])

debug = False
defaultLang1 = False
defaultLang2 = False

# ------------------------------------------------------
# glyph IDs for pre-position/pre-base chars for Tamil, like in கெ கே கை கொ கோ கௌ
# This list is for Tamil only!
# These unicode char lists must be changed for other languages!
# Please port it for other languages too!
# Other languages like Hindi or Telugu depend heavily on GPOS rules
# and may not work correctly in this GSUB based program!

langID = "tml2"  # latest form of Tamil, skip the archaic form tml2
langID2 = "taml"  # backup name if the first is not found
prepChar = ["0xbc6", "0xbc7", "0xbc8"]  # single append preposition chars list கெ கே கை
prep2Char = ["0xbca", "0xbcb", "0xbcc"]  # double append preposition chars list கொ கோ கௌ
preapp2Char = ["0xbc6", "0xbc7", "0xbc6"]  # pre-append chars
post2Char = ["0xbbe", "0xbbe", "0xbd7"]  # post-append chars
prepglyID = [0, 0, 0]  # pre-position glyph ID list initialization
prep2glyID = [0, 0, 0]  # second pre-position glyph ID list initialization
preapp2glyID = [0, 0, 0]  # pre-append glyph ID list initialization
post2glyID = [0, 0, 0]  # post-append glyph ID list initialization
uniRange = [0x0b80, 0x0bff]  # unicode range for the Tamil language
# -----------------------------------------------------

print(font2.keys())

# check if GSUB is found
GSUBfound = False
for c in font2.keys():
    if c == 'GSUB':
        print("GSUB found in the entered font file")
        GSUBfound = True

if not GSUBfound:
    print("GSUB not found in font file, quitting!")
    quit()


# parse xml tree
tree = ET.parse('temp.xml')

# getting the parent tag of
# the xml document
root = tree.getroot()

# read other link and subst data from the xml font file
substList = []  # final psts and substitution data

# first get feature list
featlist = []  # list of features in GSUB
for c in root.iter('ScriptRecord'):
    scriptrecord = c.get("index")
    for d in c.iter('ScriptTag'):
        scripttag = d.get("value")
        for e in c.iter('FeatureIndex'):
            featindex = e.get("index")
            featvalue = e.get("value")
            featlist.append([scriptrecord, scripttag, featindex, featvalue])
#print(featlist)

lookuplist = []  # list of lookup indices
for c in root.iter('FeatureRecord'):
    featurerecordindex = c.get("index")
    for d in c.iter('FeatureTag'):
        featuretag = d.get("value")
        for e in c.iter('LookupListIndex'):
            lookuplistindex = e.get("index")
            lookuplistval = e.get("value")
            lookuplist.append([featurerecordindex, featuretag, lookuplistindex, lookuplistval])
#print(lookuplist)

# check which version of tml2 or taml is present
# search whole list first
for j in range(0, len(featlist)):
    if langID == featlist[j][1]:  # check first if tml2 is found
        defaultLang1 = True
    if langID2 == featlist[j][1]:  # check first if tml2 is found
        defaultLang2 = True

#print(defaultLang1, defaultLang2)

lkList = []  # linked list

if defaultLang1:
    # print("got to 1st language")
    for j in range(0, len(featlist)):
        if langID == featlist[j][1]:  # check first if tml2 is found
            lkList.append(featlist[j][3])
            print("default language found =", langID)
    # else:
    #     print('selected font file has other languages! =', featlist[j][1])
    #     #quit()

elif defaultLang2:
    # print("got to 2nd language")
    for j in range(0, len(featlist)):
        if langID2 == featlist[j][1]:  # check if the other archaic form taml is found
                lkList.append(featlist[j][3])
                print("language found is old", langID2)


print("Feature table index: lkList =", lkList)

# now get link list of lookup tables to use in correct order
llList = []
for j in range(0, len(lookuplist)):
    for k in range(0, len(lkList)):
        if lookuplist[j][0] == lkList[k]:
            llList.append(lookuplist[j][3])
            continue
print("Lookup table index: llList =", llList)

# get char substitution list here, easier to work with glyph ID, so get glyph ID
j = 0

if not debug:

    for c in root.iter('Lookup'):
        subsetindex = c.get('index')
        for k in range(0, len(llList)):
            if llList[k] == subsetindex:  # check in right order
                for d in c.iter('LigatureSet'):
                    forglyph = font2.getGlyphID(d.get('glyph'))  # for this glyph, with glyph ID
                    for e in d.iter('Ligature'):
                        substcomp = str(e.get('components')).split(",")  # next component, split if more than 1
                        for k in range(0, len(substcomp)):
                            substcomp[k] = font2.getGlyphID(substcomp[k])
                        substglyph = font2.getGlyphID(e.get('glyph'))
                        substList.append([(forglyph),
                                          (substcomp),(substglyph)])
                        j = j + 1
                continue  # get substitute list in correct order

    print("number of substitutions to be applied in the selected language =", j)
    #print(substList)

if debug:

    # for debugging substitution list
    for c in root.iter('Lookup'):
        subsetindex = c.get('index')
        #print("subst index before", subsetindex)
        for k in range(0, len(llList)):
            if llList[k] == subsetindex:  # check in right order
                #print("subst index after", subsetindex)
                for d in c.iter('LigatureSet'):
                    forglyph = (d.get('glyph'))  # for this glyph, with glyph ID
                    #print(forglyph)
                    for e in d.iter('Ligature'):
                        substcomp = str(e.get('components')).split(",")  # next component, split if more than 1
                        for k in range(0, len(substcomp)):
                            substcomp[k] = (substcomp[k])
                        substglyph = (e.get('glyph'))
                        #print(forglyph, substcomp, substglyph)
                        substList.append([(forglyph),
                                          (substcomp),(substglyph)])
                        if (forglyph == 'tgc_ta'):
                            print("forglyph = ", [(forglyph),
                                          (substcomp),(substglyph)])
                        j = j + 1
                continue  # get substitute list in correct order

    print("number of substitutions to be made =", j)
    print(substList)
    quit()

k = 0
cmapList = []
# get mapped glyph names for unicode codes from cmap data
for Map in root.iter('map'):
    mapCode = str(Map.get('code'))
    glyphName = str(Map.get('name'))
    cmapList.append([mapCode, glyphName])
    k = k + 1
print("total number of all glyphs in cmap=", k)
#print(cmapList)

# initialize some variables
l = 0
ll = 0

# assume that they must be in the unicode fonts!
for l in range(0, len(prepChar)):
    for ll in range(0, len(cmapList)):
        if prepChar[l] == cmapList[ll][0]:
            prepglyID[l] = font2.getGlyphID(cmapList[ll][1])
            continue
#print("pre-position one char glyph IDs = ", prepglyID)  # like கெ கே கை

# assume that they must be in the unicode fonts!
for l in range(0, len(prep2Char)):
    for ll in range(0, len(cmapList)):
        if prep2Char[l] == cmapList[ll][0]:
            prep2glyID[l] = font2.getGlyphID(cmapList[ll][1])
            continue
#print("pre-position two char glyph IDs = ", prep2glyID)  # கொ கோ கௌ

# assume that they must be in the unicode fonts!
for l in range(0, len(preapp2Char)):
    for ll in range(0, len(cmapList)):
        if preapp2Char[l] == cmapList[ll][0]:
            preapp2glyID[l] = font2.getGlyphID(cmapList[ll][1])
            continue
#print("pre-append two char glyph IDs = ", preapp2glyID)  # like the ள after கௌ

# assume that they must be in the unicode fonts!
for l in range(0, len(post2Char)):
    for ll in range(0, len(cmapList)):
        if post2Char[l] == cmapList[ll][0]:
            post2glyID[l] = font2.getGlyphID(cmapList[ll][1])
            continue
#print("post-append char glyph IDs = ", post2glyID)

# print(substList)
# print(cmapList)

# open Tk window
root = Tk()
root.title('A simple Unicode to opentype glyph format converter for Affinity programs')

# create Font in default display screen object
myFont = font.Font(family='Helvetica')

# copy some sample text into clipboard for testing the program
clipboard.copy(
    "test chars \n mathi தமிழ் மொழி Mathiazhagan \n லக்‌ஷமி லக்‌ஷ்மி கை சித்து மெ விகடவீ ஶ்ரீ க்‌ஷ் மொ கை வெ றா சிந்து")
clipText = clipboard.paste()  # text will have the content of clipboard
# sanskrit characters like ஶ்ரீ or க்‌ஷ need level 3 substitution not implemented here.

# print available fonts
# print(tk_font.families())
# print(tk_font.names())

def clear_all():
    global finalDisp
    global clipText
    finalDisp = ""
    clipboard.copy(finalDisp)  # now the clipboard content will be cleared
    clipText = clipboard.paste()  # text will have the content of clipboard
    textBox.delete("1.0", END)  # clear text boxes
    textBox2.delete("1.0", END)
    print('screen and clipboard cleared')


def copy_clipboard():
    global finalDisp
    global clipText
    clipboard.copy(finalDisp)  # now the clipboard will have the data
    clipText = clipboard.paste()  # text will have the content of clipboard
    print('copy to clipboard done')


# the main routine to read copied data in the first window, do all the substitutions,
# and display the final converted file in the second window!
def retrieve_input():

    global finalDisp  # global so can be used in routines

    finalDisp = ""  # initialize final display string!

    #   manipulate the unicode string and convert
    inputValue = textBox.get("1.0", "end-1c")
    inputValue = inputValue + "   "  # pad extra 3 space for level 3

    # levels for skipping the read input chars after substitution
    level2 = False
    level3 = False
    level4 = False

    charAppend = ""  # char append variable

    for ii in range(0, len(inputValue) - 3):  # skip last 3 padded spaces

        # bypass 2 chars for double substitution, etc.
        if level2:
            level2 = False
            continue

        if level3:
            level3 = False
            continue

        if level4:
            level4 = False
            continue

        # read three consecutive chars
        inputchar = hex(ord(inputValue[ii]))
        inputchar2 = hex(ord(inputValue[ii + 1]))
        inputchar3 = hex(ord(inputValue[ii + 2]))
        inputchar4 = hex(ord(inputValue[ii + 3]))  # for skipping ZWNJ, ZWJ

        # also check if it is a LF, CR, etc. and create new row
        # assume all ascii control chars are LF or CR!
        if ord(inputValue[ii]) < 31:
            charAppend = "\n"
            finalDisp = finalDisp + charAppend  # append before exiting ii loop
            level2 = True
            continue

        # first check if current char in correct language unicode range
        # if outside, display u+ unicode, also strip 0x pattern in hex string
        elif not uniRange[0] <= ord(inputValue[ii]) <= uniRange[1]:  # unicode range correct?
            charAppend = "u+" + inputchar.replace("0x", "")
            finalDisp = finalDisp + charAppend  # append before exiting ii loop
            continue

        # get glyIDs for four consecutive chars
        for ij in range(0, len(cmapList)):
            if inputchar == cmapList[ij][0]:
                # now we have match in cmap
                glyID = font2.getGlyphID(cmapList[ij][1])  # current char glyph ID
                charAppend = "g+" + str(hex(glyID)).replace("0x", "")  # strip 0x and append g+
                break  # break ij loop to avoid looping further

        for ij in range(0, len(cmapList)):
            if inputchar2 == cmapList[ij][0]:
                # now we have match in cmap
                glyID2 = font2.getGlyphID(cmapList[ij][1])
                break

        for ij in range(0, len(cmapList)):
            if inputchar3 == cmapList[ij][0]:
                # now we have match in cmap
                glyID3 = font2.getGlyphID(cmapList[ij][1])
                break

        for ij in range(0, len(cmapList)):
            if inputchar4 == cmapList[ij][0]:
                # now we have match in cmap
                glyID4 = font2.getGlyphID(cmapList[ij][1])
                break

        # glyID3 could be ZWNJ or ZWJ, so need glyID4!
        for ij in range(0, len(cmapList)):
            if inputchar4 == cmapList[ij][0]:
                # now we have match in cmap
                glyID4 = font2.getGlyphID(cmapList[ij][1])
                break

        # print(glyID, glyID2, glyID3)

        # now check if second glyph is a preposition char and swap first and second chars
        # redefine charAppend string with swapped value
        for ij in range(0, len(prepglyID)):
            if prepglyID[ij] == (glyID2):
                charAppend = "g+" + hex(glyID2).replace("0x", "") + "g+" + hex(glyID).replace("0x", "")
                level2 = True
                continue

        for ij in range(0, len(prep2glyID)):
            if prep2glyID[ij] == (glyID2):
                charAppend = "g+" + hex(preapp2glyID[ij]).replace("0x", "") + "g+" + \
                             hex(glyID).replace("0x", "") + "g+" + hex(post2glyID[ij]).replace("0x", "")
                level2 = True
                continue

        # now look in subst GSUB map
        for ijk in range(0, len(substList)):
            if glyID == substList[ijk][0]:  # check if current char is in subst list
                # yes! now the current char is in the subst. list
                nextComp = str(substList[ijk][1])  # next char components in subst list
                nextComp = nextComp.replace("[", "")
                nextComp = nextComp.replace("]", "")
                nextComp = nextComp.split(",")  # remove [] and split if more than one value
                #print(ijk, nextComp)
                #nnextComp = str(substList[ijk][2])  # next, next comp in subst list, usu. only 2 comps

                # print("found in subst list", hex(glyID), hex(glyID2), hex(glyID3), ijk, nextSub, nextSub2)

                # this section may not work well! Not fully tested!
                if len(nextComp) > 0:  # check if next char component has one or two values
                    if len(nextComp) == 1:  # has one value
                        if glyID2 == int(nextComp[0]):
                            # print("subst level 2")
                            charAppend = "g+" + str(hex(substList[ijk][2])).replace("0x", "")
                            level2 = True
                            if len(nextComp) >= 2:  # has one value
                                level3 = True

                                # # code below does not work well, commented out!
                                # if len(nextComp) >= 2:  # has two values
                                #     # clean up 2nd component
                                #     nextComp[1] = nextComp[1].replace("", "")
                                #     if glyID4 == int(nextComp[1]):  # skip ZWNJ or ZWJ
                                #         print("got to subst level 3")
                                #         charAppend = str(hex(substList[ijk][2])).replace("0x", "")
                                #         charAppend = charAppend[:-1]
                                #         charAppend = "g+" + charAppend
                                #         # charAppend = "g+" + str(hex(substList[ijk][2])).replace("0x", "")
                                #         print(nextComp, charAppend)
                                #         finalDisp = finalDisp + charAppend
                                #          #print(finalDisp)
                                #         level4 = True
                                #         level3 = True
                                #         continue


        finalDisp = finalDisp + charAppend
        #print(finalDisp)

    # print(finalDisp)

    print('conversion done')
    textBox2.insert(INSERT, finalDisp)


# display first text box using std font
textBox = Text(root, height=10, width=100, font=myFont)
textBox.pack()

# display second text box using target font
textBox2 = Text(root, height=10, width=100, font=myFont)
textBox2.pack(pady=20)

# button clicks section
buttonCommit = Button(root, height=1, width=10, text="Convert", font=myFont,
                      command=lambda: retrieve_input())
# command=lambda: retrieve_input() >>> just means do this when i press the button
buttonCommit.pack()

buttonCommit2 = Button(root, height=1, width=10, text="Copy", font=myFont,
                       command=lambda: copy_clipboard())
# command=lambda: retrieve_input() >>> just means do this when i press the button
buttonCommit2.pack()

buttonCommit3 = Button(root, height=1, width=10, text="Clear", font=myFont,
                       command=lambda: clear_all())
# command=lambda: retrieve_input() >>> just means do this when i press the button
buttonCommit3.pack()

mainloop()
