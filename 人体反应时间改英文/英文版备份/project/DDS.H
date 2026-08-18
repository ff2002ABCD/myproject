//use SPI mode 1 12.5Mhz and P20
//design for AD9833
//NOT REAL-TIME INTERFACE
//CALL WHEN SPIBF==0
#ifndef DDS_H
#define DDS_H

#define PDDS P20

#include "SPI.H"
#include ""

extern void ddsRst();
extern void ddsSetF(unsigned long fn);	//28bits F0
extern void ddsSetP(unsigned int pn);	//12 bits P0
extern void ddsCfg(unsigned int cfg);	//config data
extern void ddsProc();					//1ms

#endif