@echo off
copy .\MSCOMM32.OCX %SYSTEMROOT%\system32
regsvr32 MSCOMM32.OCX