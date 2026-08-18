//TMR2L专用中断

#ifndef DISPLCD_H
#define DISPLCD_H

#include "C8051F410X.H"
#include "SPI.h"

extern void (*dispSvProc) ();
extern void (*dispFDProc) ();
#define LCDCHR 4		//行数
#define LCDCHC 16		//列数
#define DISPEN ET2 

extern bit dispSelCG;
extern unsigned char dispData[LCDCHR][LCDCHC];

extern void dispRefreshSt();
extern void dispRst();
extern void dispCopy(unsigned char code p[LCDCHR][LCDCHC]);
extern void dispSelSt(unsigned char);
extern void lcdGCrSt();
extern void dispSt();
extern void dispInt();
extern void dispSvNull();
extern void dispTs();
extern void dispFD();	//100ms

#define PDCS P22
#define PDRST P21
#define disp180usTN 16
#define DISPTN 166		//20us

#endif