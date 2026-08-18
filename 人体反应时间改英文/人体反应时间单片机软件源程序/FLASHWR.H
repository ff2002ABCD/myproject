//FLASH¶ÁÐ´
#ifndef FLASHWR_H
#define FLASHWR_H

#include "C8051F410X.H"

#define FLASHDATAADDR 0x2000
#define FLASHDATASIZE 10		//FLASHDATASIZE<=255
#define FLASHON 0x01	//FLASHÓÐÐ§

//-----------------------------------------------------------------------------
// Function Prototypes
//-----------------------------------------------------------------------------
extern void flashWrite (unsigned char index,unsigned char byte);
extern unsigned char flashRead (unsigned char index);
extern void flashPageErase ();
extern void flashChange (unsigned char index,unsigned char byte);
extern void flashInit();
extern void flashChangeI(unsigned char index,unsigned int dataI);	
extern unsigned int flashReadI(unsigned char index);

#endif		