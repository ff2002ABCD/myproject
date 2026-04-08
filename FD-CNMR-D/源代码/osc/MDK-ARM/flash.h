#ifndef __FLASH_H
#define __FLASH_H

void load_writedata();
void load_writedata_1();
void load_calibo_data();
void load_current();
void STMFLASH_OnlyWrite(uint32_t WriteAddr,uint32_t *pBuffer,uint32_t NumToWrite);
extern uint32_t Flash_WData[8];
extern uint32_t Flash_WData_1[8];
#endif