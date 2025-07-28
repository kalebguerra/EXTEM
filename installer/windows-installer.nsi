# NSIS Installer Script for AI Image Generator Manager
# This creates a Windows installer with proper desktop integration

!define APPNAME "AI Image Generator Manager"
!define COMPANYNAME "AI Manager Team"
!define DESCRIPTION "Advanced desktop application for AI image generation management"
!define VERSIONMAJOR 2
!define VERSIONMINOR 0
!define VERSIONBUILD 0
!define HELPURL "https://github.com/your-repo/ai-generator"
!define UPDATEURL "https://github.com/your-repo/ai-generator/releases"
!define ABOUTURL "https://github.com/your-repo/ai-generator"
!define INSTALLSIZE 150000

RequestExecutionLevel admin
InstallDir "$PROGRAMFILES\${APPNAME}"
Name "${APPNAME}"
Icon "assets\icon.ico"
outFile "AI-Image-Generator-Manager-Setup.exe"

!include LogicLib.nsh
!include MUI2.nsh

# Modern UI Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "assets\icon.ico"
!define MUI_UNICON "assets\icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "assets\installer-banner.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "assets\installer-banner.bmp"

# Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

section "install"
    # Files to install
    setOutPath $INSTDIR
    file /r "dist\*"
    
    # Create desktop shortcut
    createShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\AI Image Generator Manager.exe" "" "$INSTDIR\icon.ico"
    
    # Create start menu shortcuts
    createDirectory "$SMPROGRAMS\${APPNAME}"
    createShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\AI Image Generator Manager.exe" "" "$INSTDIR\icon.ico"
    createShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    
    # Registry entries for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\icon.ico$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
    
    # Create uninstaller
    writeUninstaller "$INSTDIR\uninstall.exe"
sectionEnd

section "uninstall"
    # Remove files
    rmDir /r "$INSTDIR"
    
    # Remove shortcuts
    delete "$DESKTOP\${APPNAME}.lnk"
    rmDir /r "$SMPROGRAMS\${APPNAME}"
    
    # Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
sectionEnd