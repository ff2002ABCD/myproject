#include <C8051F410.H>
#include "spi.h"

bit spiBF;
void (* spiSV)();

void spiRst()
{
	spiBF=0;
	spiSV=spiNULL;
}

void spi_INT () interrupt INTERRUPT_SPI0 using 1
{
	SPI0CN &= 0x0f;
	(* spiSV)();
}

void spiTrans(unsigned char tsdata)
{
	SPI0DAT=tsdata;
}

unsigned char spiBusy()
{
	if(SPI0CFG & 0X80) return 1;
	return 0;
}

void spiNULL() {}
