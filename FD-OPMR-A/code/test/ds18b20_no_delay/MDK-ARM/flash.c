#include "main.h"
#include "stdio.h"
#include "flash.h"
#include "osc.h"


//h750flash 0x 0800 0000 - 0x 0801 FFFF 128K
//数据存放 从 0x0801 9000 开始

extern TIM_HandleTypeDef htim3;
uint32_t Flash_WData[8] ={0xAAAAAAAA,0xBBBBBBBB,0xCCCCCCCC,0xDDDDDDDD,0xAAAAAAAA,0xAAAAAAAA,0xAAAAAAAA,0xAAAAAAAA};


static FLASH_EraseInitTypeDef EraseInitStruct = {
	.TypeErase = FLASH_TYPEERASE_SECTORS,       //扇区擦除
	.Banks= FLASH_BANK_1,
	.Sector = FLASH_SECTOR_7,                //擦除地址
	.NbSectors = 1,     	//擦除扇区数
	.VoltageRange = FLASH_VOLTAGE_RANGE_3
};
void load_writedata()
{	
	Flash_WData[0] = 1000.000+1000.000*del_zero_ch1;
	Flash_WData[1] = 1000.000+1000.000*del_zero_ch2;
	Flash_WData[2] = 1000.000+100000.000*del_k_ch1;
  Flash_WData[3] = 1000.000+100000.000*del_k_ch2;
}

void STMFLASH_OnlyWrite(uint32_t WriteAddr,uint32_t *pBuffer,uint32_t NumToWrite)
{
	if(*(__IO uint32_t*)0x08019000!=0xffffffff)return;
	HAL_StatusTypeDef FlashStatus=HAL_OK;
	uint32_t endaddr=0;	
	
	HAL_FLASH_Unlock();       
	endaddr=WriteAddr+NumToWrite*4;	
	
		while(WriteAddr<endaddr)
		{
      if(HAL_FLASH_Program(FLASH_TYPEPROGRAM_FLASHWORD,WriteAddr,(uint64_t)pBuffer)!=HAL_OK)//????
			{ 
				printf("t3.txt=\"error\"\xff\xff\xff");
				break;
			}
			WriteAddr+=32;
			pBuffer+=8;
		} 
	HAL_FLASH_Lock();
}

void load_calibo_data()
{
	Flash_WData[0]=*(__IO uint32_t*)0x08019000;
	Flash_WData[1]=*(__IO uint32_t*)0x08019004;
	Flash_WData[2]=*(__IO uint32_t*)0x08019008;
	Flash_WData[3]=*(__IO uint32_t*)0x0801900C;
	del_zero_ch1=((int32_t)(*(__IO uint32_t*)0x08019000)-1000.000)/1000.000;
	del_zero_ch2=((int32_t)(*(__IO uint32_t*)0x08019004)-1000.000)/1000.000;
	del_k_ch1=(((int32_t)(*(__IO uint32_t*)0x08019008)-1000.000000))/100000.000000;
	del_k_ch2=((int32_t)(*(__IO uint32_t*)0x0801900C)-1000.000000)/100000.000000;
}
