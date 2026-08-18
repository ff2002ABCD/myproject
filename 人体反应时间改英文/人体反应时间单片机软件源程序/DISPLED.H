//use SPI connnect with MAX7219 in mode0 200kbps
#ifndef DISPLED_H
#define DISPLED_H

#include "SPI.H"

#define PCS P22

extern void displedRefresh();		//trans displedData to MAX7219
extern void displedSetNum(unsigned char num);		//set led number
extern void displedTurnOn();		//turn on led
extern void displedTurnOff();		//turn off led
extern void displedSetIntens(unsigned char its);		//set led intensity
extern void displedRst();			//reset	turn on led decode mode B displedData=0;
extern void displedSetDM(unsigned char dm);			//set decode mode
extern void displedProc();			//1ms

extern unsigned char displedData[8];

#endif
