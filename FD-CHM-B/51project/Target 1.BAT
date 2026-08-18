SET C51INC=C:\Keil_v5\C51\Inc;C:\Keil_v5\C51\Inc\Cygnal
SET C51LIB=C:\Keil_v5\C51\Lib
SET CPU_TYPE=C8051F410
SET CPU_VENDOR=Silicon Labs
SET UV2_TARGET=Target 1
SET CPU_XTAL=0x00B71B00
"C:\Keil_v5\C51\BIN\AX51.EXE" @".\Objects\STARTUP._ia"
"C:\Keil_v5\C51\BIN\C51.EXE" @".\Objects\main.__i"
"C:\Keil_v5\C51\BIN\LX51.EXE" @".\Objects\51.lnp"
"C:\Keil_v5\C51\BIN\OHX51.EXE" ".\Objects\51" HEX
