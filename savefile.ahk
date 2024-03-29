#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn All, StdOut  ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.
SetControlDelay -1

Sleep 500 ; script seems to be a little inconsistent, hopefully this helps fix it

WinWait Save As ahk_exe chrome.exe
WinActivate
ControlSetText Edit1, %1%
Sleep 500
ControlClick &Save

Sleep 250

; Confirm overwrite if required
IfWinExist Confirm Save As
{
WinActivate
ControlClick &Yes
}