#include "flash.h"


//debug 查看对应地址，是否正确，如果显示的是问号，则无此位置
//RCT6 256k  最大地址 0x0803FFE0
#define FLASH_SAVE_ADDR  0x08009000

static FLASH_EraseInitTypeDef EraseInitStruct = {
	.TypeErase = FLASH_TYPEERASE_PAGES,       //页擦除
	.PageAddress = FLASH_SAVE_ADDR,                //擦除地址
	.NbPages = 1                              //擦除页数
};

void Flash_writeData()
{
	HAL_FLASH_Unlock();
	uint32_t PageError = 0;
	__disable_irq();                             //擦除前关闭中断
	if (HAL_FLASHEx_Erase(&EraseInitStruct,&PageError) == HAL_OK)
	{
			printf("擦除成功\r\n");
	}
	__enable_irq();                             //擦除后打开中断
	
	uint32_t writeFlashData=0x12;
	
	uint32_t addr = 0x08009000;                  //写入的地址
	HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD,addr, writeFlashData);
	printf("at address:0x%x, read value:0x%x\r\n", addr, *(__IO uint32_t*)addr);
	HAL_FLASH_Lock();
}

void Flash_writeK()
{
	HAL_FLASH_Unlock();
	uint32_t PageError = 0;
	__disable_irq();                             //擦除前关闭中断
	if (HAL_FLASHEx_Erase(&EraseInitStruct,&PageError) == HAL_OK)
	{
			printf("擦除成功\r\n");
	}
	__enable_irq();                             //擦除后打开中断
	
	uint32_t writeFlashData=k*100;
	
	uint32_t addr = 0x08009000;                  //写入的地址
	HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD,addr, writeFlashData);
	printf("k.txt=\"ok\"\xff\xff\xff");
//	printf("at address:0x%x, read value:0x%x\r\n", addr, *(__IO uint32_t*)addr);
	HAL_FLASH_Lock();
}