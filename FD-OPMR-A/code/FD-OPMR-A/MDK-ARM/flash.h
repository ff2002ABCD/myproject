#ifndef __FLASH_H
#define __FLASH_H

void load_writedata();
void load_calibo_data();
void STMFLASH_OnlyWrite(uint32_t WriteAddr,uint32_t *pBuffer,uint32_t NumToWrite);
extern uint32_t Flash_WData[8];
#endif