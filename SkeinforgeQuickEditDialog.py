#!/usr/bin/env python

from skeinforge.fabmetheus_utilities import archive
from skeinforge.fabmetheus_utilities import settings
from skeinforge.skeinforge_application.skeinforge_utilities import skeinforge_craft
from skeinforge.skeinforge_application.skeinforge_utilities import skeinforge_profile
from skeinforge.skeinforge_application.skeinforge_plugins.profile_plugins import extrusion
import os
import wx
import fileinput
import sys

class SkeinforgeQuickEditDialog(wx.Dialog):
    '''Shows a consise list of important settings from the active Skeinforge profile.'''
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX | wx.RESIZE_BORDER
        wx.Dialog.__init__(self, *args, **kwds)
        self.okButton = wx.Button(self, wx.ID_OK, "Save")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "")
        self.Bind(wx.EVT_BUTTON, self.OnExit, self.cancelButton)
        self.Bind(wx.EVT_BUTTON, self.OnSave, self.okButton)

        '''
            The following list determines whaich settings are shown.  
            The dictionary key is the plugin name and the value is a list of setting names as found in the corresponding .csv file for that plugin.
            
            NOTE:  Skeinforge is tightly integrated with Tkinter and there appears to be a dependency which stops radio-button values from being saved.
                   Perhaps this can be solved, but at the moment this dialog cannot modify radio button values.  One will have to use the main Skeinforge application.  
        '''
        self.moduleSettingsMap = {
                                'bottom':['Activate Bottom', 'Additional Height over Layer Thickness (ratio):'],
                                'carve':['Layer Thickness (mm):', 'Perimeter Width over Thickness (ratio):'],
                                'cool':['Activate Cool', 'Minimum Layer Time (seconds):'],
                                'dimension':['Extruder Retraction Speed (mm/s):', 'Retraction Distance (millimeters):'],
                                'fill':['Activate Fill:', 'Extra Shells on Alternating Solid Layer (layers):', 'Extra Shells on Base (layers):', 'Extra Shells on Sparse Layer (layers):', 'Infill Solidity (ratio):', 'Solid Surface Thickness (layers):'],
                                'multiply':['Activate Multiply:', 'Center X (mm):', 'Center Y (mm):', 'Number of Columns (integer):', 'Number of Rows (integer):'],
                                'raft':['Activate Raft', 'Add Raft, Elevate Nozzle, Orbit:', 'Object First Layer Feed Rate Infill Multiplier (ratio):', 'Object First Layer Feed Rate Perimeter Multiplier (ratio):', 'Object First Layer Flow Rate Infill Multiplier (ratio):', 'Object First Layer Flow Rate Perimeter Multiplier (ratio):'],
                                'speed':['Activate Speed:', 'Add Flow Rate:', 'Feed Rate (mm/s):', 'Flow Rate Setting (float):', 'Perimeter Feed Rate over Operating Feed Rate (ratio):', 'Perimeter Flow Rate over Operating Flow Rate (ratio):', 'Travel Feed Rate (mm/s):']
                               }

        self.scrollbarPanel = wx.ScrolledWindow(self, -1, style=wx.TAB_TRAVERSAL)
        self.settingsSizer = self.getProfileSettings()
        self.scrollbarPanel.SetSizer(self.settingsSizer)

        self.__set_properties()
        self.__do_layout()
        self.Show()

    def __set_properties(self):
        self.profileName = skeinforge_profile.getProfileName(skeinforge_profile.getCraftTypeName())
        self.SetTitle("Skeinforge Quick Edit Profile: " + self.profileName)

        # For some reason the dialog size is not consistent between Windows and Linux - this is a hack to get it working 
        if (os.name == 'nt'):
            self.SetMinSize(wx.DLG_SZE(self, (465, 370)))
        else:
            self.SetSize(wx.DLG_SZE(self, (465, 325)))

        self.SetPosition((0, 0))
        self.CenterOnParent()
        self.scrollbarPanel.SetScrollRate(10, 10)

    def __do_layout(self):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        actionsSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(self.scrollbarPanel, 1, wx.EXPAND | wx.ALL, 5)
        actionsSizer.Add(self.okButton, 0, 0, 0)
        actionsSizer.Add(self.cancelButton, 0, wx.LEFT, 10)
        mainSizer.Add(actionsSizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        self.SetSizer(mainSizer)
        self.Layout()

    def getProfileSettings(self):
        settingsSizer = wx.GridBagSizer(hgap=2, vgap=2)
        settingsRow = 0

        for craftName in sorted(self.moduleSettingsMap.keys()):

            craftStaticBox = wx.StaticBox(self.scrollbarPanel, -1, craftName.capitalize())
            craftStaticBoxSizer = wx.StaticBoxSizer(craftStaticBox, wx.VERTICAL)

            # For some reason the dialog size is not consistent between Windows and Linux - this is a hack to get it working
            if (os.name == 'nt'):
                craftStaticBoxSizer.SetMinSize((320, -1))
            else:
                craftStaticBoxSizer.SetMinSize((450, -1))
            pluginModule = archive.getModuleWithPath(os.path.join(skeinforge_craft.getPluginsDirectoryPath(), craftName))
            repo = pluginModule.getNewRepository()

            for setting in settings.getReadRepository(repo).preferences:
                if setting.name in self.moduleSettingsMap[craftName]:

                    settingSizer = wx.GridBagSizer(hgap=2, vgap=2)
                    settingSizer.AddGrowableCol(0)
                    settingRow = 0
                    settingLabel = wx.StaticText(self.scrollbarPanel, -1, setting.name)
                    settingLabel.Wrap(400)
                    settingSizer.Add(settingLabel, pos=(settingRow, 0))

                    if (isinstance(setting.value, bool)):
                        checkbox = wx.CheckBox(self.scrollbarPanel)
                        checkbox.SetName(craftName + '.' + setting.name)
                        checkbox.SetValue(setting.value)
                        settingSizer.Add(checkbox, pos=(settingRow, 1))
                        settingSizer.AddSpacer((25, -1), pos=(settingRow, 2))
                    else:
                        textCtrl = wx.TextCtrl(self.scrollbarPanel, value=str(setting.value), size=(50, -1))
                        textCtrl.SetName(craftName + '.' + setting.name)
                        settingSizer.Add(textCtrl, pos=(settingRow, 1))

                    craftStaticBoxSizer.Add(settingSizer, 1, wx.EXPAND, 0)
                    settingRow += 1
            col = settingsRow % 2
            settingsSizer.Add(craftStaticBoxSizer, pos=(settingsRow - col, col))
            settingsRow += 1

        return settingsSizer

    def OnExit(self, e):
        self.Destroy()

    def OnSave(self, e):
        for x in self.scrollbarPanel.GetChildren():
            if (isinstance(x, (wx.CheckBox, wx.TextCtrl))):
                name = x.GetName().partition('.')
                craftName = name[0]
                settingName = name[2]
                pluginModule = archive.getModuleWithPath(os.path.join(skeinforge_craft.getPluginsDirectoryPath(), craftName))
                repo = pluginModule.getNewRepository()

                for setting in settings.getReadRepository(repo).preferences:
                    if setting.name == settingName:
                        if setting.value == None or str(x.GetValue()) != str(setting.value):
                            self.saveSetting(repo, settingName, setting.value, x.GetValue())
        print("Skeinforge settings have been saved.")
        self.Destroy()

    def saveSetting(self, repo, name, oldValue, newValue):
        repoSettingsFilename = os.path.join(archive.getProfilesPath() , settings.getProfileBaseName(repo))
        if (type(oldValue).__name__ == 'float'):
            newValue = '{0:g}'.format(float(newValue))
        for line in fileinput.FileInput(repoSettingsFilename, inplace=1):
            if line.startswith(name + "\t"):
                line = "{0}\t{1}\n".format(name, str(newValue))
            sys.stdout.write(line)
        print('Saved: ' + name + ' = ' + str(newValue) + ' (was: ' + str(oldValue) + ')')

class SkeinforgeQuickEditApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        SkeinforgeQuickEditDialog(None, -1, "")
        return 1

if __name__ == "__main__":
    skeinforgeQuickEditApp = SkeinforgeQuickEditApp(0)
    skeinforgeQuickEditApp.MainLoop()
