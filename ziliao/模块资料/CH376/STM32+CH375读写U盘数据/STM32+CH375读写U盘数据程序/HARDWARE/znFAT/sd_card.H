#ifndef __SDX1_H__
#define __SDX1_H__


#include "sd_type.h"

#include "stm32f10x.h"




#define SET_SD1_CS_PIN(val)  (val?GPIO_SetBits(GPIOD, GPIO_Pin_11):GPIO_ResetBits(GPIOD, GPIO_Pin_11))

#define TRY_TIME 200   //向SD卡写入命令之后，读取SD卡的回应次数，即读TRY_TIME次，如果在TRY_TIME次中读不到回应，产生超时错误，命令写入失败

//相关宏定义
//-------------------------------------------------------------
#define SD_VER_ERR     0X00
#define SD_VER_MMC     0X01
#define SD_VER_V1      0X02
#define SD_VER_V2      0X03
#define SD_VER_V2HC    0X04

#define INIT_ERROR                  0x01 //初始化错误
#define INIT_CMD0_ERROR             0x02 //CMD0错误
#define INIT_CMD1_ERROR             0x03 //CMD1错误
#define INIT_SDV2_ACMD41_ERROR	    0x04 //ACMD41错误
#define INIT_SDV1_ACMD41_ERROR	    0x05 //ACMD41错误

#define WRITE_CMD24_ERROR           0x06 //写块时产生CMD24错误
#define WRITE_BLOCK_ERROR           0x07 //写块错误

#define READ_BLOCK_ERROR            0x08 //读块错误

#define WRITE_CMD25_ERROR           0x09 //在连续多块写时产生CMD25错误
#define WRITE_NBLOCK_ERROR          0x0A //连续多块写失败

#define READ_CMD18_ERROR            0x0B //在连续多块读时产生CMD18错误
 
#define GET_CSD_ERROR               0x0C //读CSD失败

//-------------------------------------------------------------
UINT8 SD1_Init(void); //SD卡初始化

UINT8 SD1_Write_Sector(UINT32 addr,UINT8 *buffer); //将buffer数据缓冲区中的数据写入地址为addr的扇区中
UINT8 SD1_Read_Sector(UINT32 addr,UINT8 *buffer);	 //从地址为addr的扇区中读取数据到buffer数据缓冲区中
UINT8 SD1_Write_nSector(UINT32 nsec,UINT32 addr,UINT8 *buffer); //将buffer数据缓冲区中的数据写入起始地址为addr的nsec个连续扇区中
UINT8 SD1_Read_nSector(UINT32 nsec,UINT32 addr,UINT8 *buffer); //将buffer数据缓冲区中的数据写入起始地址为addr的nsec个连续扇区中
UINT8 SD1_Erase_nSector(UINT32 addr_sta,UINT32 addr_end);
UINT32 SD1_GetTotalSec(void); //获取SD卡的总扇区数


u8 SPI_SD_SendReadByte(u8 TxData);
void SD_Flash_Init(u8 SPI_BaudRatePrescaler);

void SD1_SPI_SPEED_LOW(void);
void SD1_SPI_SPEED_HIGH(void);

#endif
