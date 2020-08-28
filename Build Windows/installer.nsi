!define VERSION "0.9"
SetCompressor lzma

; The name of the installer
Name "Snu Clipboard Manager ${VERSION}"

; The file to write
OutFile "Snu Clipboard Manager Installer v${VERSION}.exe"

; The default installation directory
InstallDir "$PROGRAMFILES64\Snu Clipboard Manager"

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\Snu Clipboard Manager" "Install_Dir"

; Request application privileges for Windows Vista
RequestExecutionLevel admin

AllowRootDirInstall true

Icon "icon.ico"


;--------------------------------

; Pages

Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles


;--------------------------------

; The stuff to install
Section "!Snu Clipboard Manager (Required)"

  SectionIn RO
  
  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  
  ; Put files there
  File /r *

  ; Write the installation path into the registry
  WriteRegStr HKLM "SOFTWARE\Snu Clipboard Manager" "Install_Dir" "$INSTDIR"

  SectionEnd
  
Section "Create Uninstaller"

  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Snu Clipboard Manager" "DisplayName" "Snu Clipboard Manager"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Snu Clipboard Manager" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Snu Clipboard Manager" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Snu Clipboard Manager" "NoRepair" 1
  WriteUninstaller "uninstall.exe"
  
SectionEnd

; Optional section (can be disabled by the user)
Section "Create Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\Snu Clipboard Manager"
  CreateShortcut "$SMPROGRAMS\Snu Clipboard Manager\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortcut "$SMPROGRAMS\Snu Clipboard Manager\Snu Clipboard Manager.lnk" "$INSTDIR\Snu Clipboard Manager.exe" "" "$INSTDIR\Snu Clipboard Manager.exe" 0
  
SectionEnd

Section /o "Create Desktop Shortcut"

  CreateShortcut "$DESKTOP\Snu Clipboard Manager.lnk" "$INSTDIR\Snu Clipboard Manager.exe" "" "$INSTDIR\Snu Clipboard Manager.exe" 0

SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Snu Clipboard Manager"
  DeleteRegKey HKLM "SOFTWARE\Snu Clipboard Manager"

  ; Remove files and uninstaller
  Delete "$INSTDIR\*"
  Delete $INSTDIR\uninstall.exe

  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\Snu Clipboard Manager\*.*"
  Delete "$DESKTOP\Snu Clipboard Manager.lnk"

  ; Remove directories used
  
  RMDir /r "$INSTDIR\data"
  RMDir /r "$INSTDIR\help"
  RMDir /r "$INSTDIR\include"
  RMDir /r "$INSTDIR\kivy"
  RMDir /r "$INSTDIR\kivy_install"
  RMDir /r "$INSTDIR\win32com"
  RMDir "$SMPROGRAMS\Snu Clipboard Manager"
  RMDir "$INSTDIR"

SectionEnd
