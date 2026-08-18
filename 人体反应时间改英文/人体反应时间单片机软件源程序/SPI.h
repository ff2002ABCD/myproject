#ifndef SPI_H
#define SPI_H

#include "C8051F410X.H"

#define SPI0CFGN 0X40	//MODE 0
#define SPI0CKRN 0X3C	//200K

extern void spiRst();
extern void spiNULL();

extern bit spiBF;			//using SPI interface
extern void (* spiSV)();	//using 1
unsigned char spiBusy();	//if SPI in transporting return 1 else 0 
void spiTrans(unsigned char tsdata); //trans tsdata by SPI

#endif