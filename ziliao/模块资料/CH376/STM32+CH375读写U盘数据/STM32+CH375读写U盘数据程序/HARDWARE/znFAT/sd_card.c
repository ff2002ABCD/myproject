#include "sd_card.h"
#include "myfun.h"
#include "sd_type.h"

//变量定义
//--------------------------------------------------------------

UINT8 SD1_Addr_Mode=0; //SD1的寻址方式，1为块寻址，0为字节寻址
UINT8 SD1_Ver=SD_VER_ERR; //SD卡1的版本
//---------------------------------------------------------------

#define SD1_SPI_WByte(x) SPI_SD_SendReadByte(x)

#define SD1_SPI_RByte()  SPI_SD_SendReadByte(0XFF)

void SD_Flash_Init(u8 SPI_BaudRatePrescaler)
{
	GPIO_InitTypeDef GPIO_InitStruct;
	SPI_InitTypeDef SPI_InitStruct;
	
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOD|RCC_APB2Periph_GPIOA|RCC_APB2Periph_SPI1 ,ENABLE);
	
	//SPI1管脚初始化成SPI功能
	GPIO_InitStruct.GPIO_Pin = GPIO_Pin_5 | GPIO_Pin_7;
	GPIO_InitStruct.GPIO_Speed = GPIO_Speed_10MHz;
	GPIO_InitStruct.GPIO_Mode = GPIO_Mode_AF_PP;
	GPIO_Init(GPIOA, &GPIO_InitStruct);
	
	//MISO管脚
	GPIO_InitStruct.GPIO_Pin = GPIO_Pin_6;
	GPIO_InitStruct.GPIO_Mode = GPIO_Mode_AF_OD;
	GPIO_Init(GPIOA, &GPIO_InitStruct);
	
	//FLASH_CS管脚
	GPIO_InitStruct.GPIO_Pin = GPIO_Pin_11;
	GPIO_InitStruct.GPIO_Mode = GPIO_Mode_Out_PP;
	GPIO_Init(GPIOD, &GPIO_InitStruct);
	SET_SD1_CS_PIN(1);
	
	//SPI1初始化
	SPI_InitStruct.SPI_Direction = SPI_Direction_2Lines_FullDuplex;
	SPI_InitStruct.SPI_Mode = SPI_Mode_Master;
	SPI_InitStruct.SPI_DataSize = SPI_DataSize_8b;
	SPI_InitStruct.SPI_CPOL = SPI_CPOL_High;
	SPI_InitStruct.SPI_CPHA = SPI_CPHA_2Edge;
	
	SPI_InitStruct.SPI_NSS = SPI_NSS_Soft;/*SPI_NSS_Hard;*/
	SPI_InitStruct.SPI_BaudRatePrescaler = SPI_BaudRatePrescaler_8;
	SPI_InitStruct.SPI_FirstBit = SPI_FirstBit_MSB;
	SPI_InitStruct.SPI_CRCPolynomial = 7;
	SPI_Init(SPI1, &SPI_InitStruct);

	/* Enable SPI1  */
	SPI_Cmd(SPI1, ENABLE);

}

u8 SPI_SD_SendReadByte(u8 TxData)
{

	while(SPI_I2S_GetFlagStatus(SPI1,SPI_I2S_FLAG_TXE)==RESET);
	
	SPI_I2S_SendData(SPI1, TxData);

    /* Wait to receive a Half Word */
  while (SPI_I2S_GetFlagStatus(SPI1, SPI_I2S_FLAG_RXNE) == RESET);

    /* Return the Half Word read from the SPI bus */
  return SPI_I2S_ReceiveData(SPI1);
}

void SD1_SPI_SPEED_LOW(void) 
{
	SD_Flash_Init(SPI_BaudRatePrescaler_128); 
}

void SD1_SPI_SPEED_HIGH(void)
{
	SD_Flash_Init(SPI_BaudRatePrescaler_4); 
}

UINT8 SD1_SPI_Init(void)
{
 SD_Flash_Init(SPI_BaudRatePrescaler_128); //SPI接口初始化
	
 return 0;
}

/******************************************************************
 - 功能描述：向SD卡写命令
 - 参数说明：SD卡的命令是6个字节，pcmd是指向命令字节序列的指针
 - 返回说明：命令写入不成功，将返回0xff
 ******************************************************************/

UINT8 SD1_Write_Cmd(UINT8 *pcmd) 
{
 UINT8 r=0,time=0;
 
 SET_SD1_CS_PIN(1);
 SD1_SPI_WByte(0xFF); //发送8个时钟，提高兼容性，如果没有这里，有些SD卡可能不支持   
	
 SET_SD1_CS_PIN(0);
 while(0XFF!=SD1_SPI_RByte()); //等待SD卡准备好，再向其发送命令

 //将6字节的命令序列写入SD卡
 SD1_SPI_WByte(pcmd[0]);
 SD1_SPI_WByte(pcmd[1]);
 SD1_SPI_WByte(pcmd[2]);
 SD1_SPI_WByte(pcmd[3]);
 SD1_SPI_WByte(pcmd[4]);
 SD1_SPI_WByte(pcmd[5]);
	
 if(pcmd[0]==0X1C) SD1_SPI_RByte(); //如果是停止命令，跳过多余的字节

 do 
 {  
  r=SD1_SPI_RByte();
  time++;
 }while((r&0X80)&&(time<TRY_TIME)); //如果重试次数超过TRY_TIME则返回错误

 return r;
}

/******************************************************************
 - 功能描述：SD卡初始化，针对于不同的SD卡，如MMC、SD或SDHC，初始化
             方法是不同的
 - 参数说明：无
 - 返回说明：调用成功，返回0x00，否则返回错误码
 ******************************************************************/

UINT8 SD1_Init(void)
{
 UINT8 time=0,r=0,i=0;
	
 UINT8 rbuf[4]={0};
	
 UINT8 pCMD0[6] ={0x40,0x00,0x00,0x00,0x00,0x95}; //CMD0，将SD卡从默认上电后的SD模式切换到SPI模式，使SD卡进入IDLE状态
 UINT8 pCMD1[6] ={0x41,0x00,0x00,0x00,0x00,0x01}; //CMD1，MMC卡使用CMD1命令进行初始化
 UINT8 pCMD8[6] ={0x48,0x00,0x00,0x01,0xAA,0x87}; //CMD8，用于鉴别SD卡的版本，并可从应答得知SD卡的工作电压
 UINT8 pCMD16[6]={0x50,0x00,0x00,0x02,0x00,0x01}; //CMD16，设置扇区大小为512字节，此命令用于在初始化完成之后进行试探性的操作，
                                                          //如果操作成功，说明初始化确实成功
 UINT8 pCMD55[6]={0x77,0x00,0x00,0x00,0x00,0x01}; //CMD55，用于告知SD卡后面是ACMD，即应用层命令 CMD55+ACMD41配合使用
                                                          //MMC卡使用CMD1来进行初始化，而SD卡则使用CMD55+ACMD41来进行初始化
 UINT8 pACMD41H[6]={0x69,0x40,0x00,0x00,0x00,0x01}; //ACMD41,此命令用于检测SD卡是否初始化完成，MMC卡，不适用此命令，针对2.0的SD卡
 UINT8 pACMD41S[6]={0x69,0x00,0x00,0x00,0x00,0x01}; //ACMD41,此命令用于检测SD卡是否初始化完成，MMC卡，不适用此命令，针对1.0的SD卡

 UINT8 pCMD58[6]={0x7A,0x00,0x00,0x00,0x00,0x01}; //CMD58，用于鉴别SD2.0到底是SDHC，还是普通的SD卡，二者对扇区地址的寻址方式不同
 
 SD1_SPI_Init(); //SPI接口相关初始化

 SD1_SPI_SPEED_LOW(); //首先将SPI切为低速
	
 SET_SD1_CS_PIN(1); 
	
 for(i=0;i<0x0f;i++) //首先要发送最少74个时钟信号，这是必须的！激活SD卡
 {
  SD1_SPI_WByte(0xff); //120个时钟
 }

 time=0;
 do
 { 
  r=SD1_Write_Cmd(pCMD0);//写入CMD0
  time++;
  if(time>=TRY_TIME) 
  { 
   return(INIT_CMD0_ERROR);//CMD0写入失败
  }
 }while(r!=0x01);
 
 if(1==SD1_Write_Cmd(pCMD8))//写入CMD8，如果返回值为1，则SD卡版本为2.0
 {
	rbuf[0]=SD1_SPI_RByte(); rbuf[1]=SD1_SPI_RByte(); //读取4个字节的R7回应，通过它可知此SD卡是否支持2.7~3.6V的工作电压
	rbuf[2]=SD1_SPI_RByte(); rbuf[3]=SD1_SPI_RByte();
	 
	if(rbuf[2]==0X01 && rbuf[3]==0XAA)//SD卡是否支持2.7~3.6V
	{		
	 time=0;
	 do
	 {
		SD1_Write_Cmd(pCMD55);//写入CMD55
		r=SD1_Write_Cmd(pACMD41H);//写入ACMD41，针对SD2.0
		time++;
    if(time>=TRY_TIME) 
    { 
     return(INIT_SDV2_ACMD41_ERROR);//对SD2.0使用ACMD41进行初始化时产生错误
    }
   }while(r!=0);	

   if(0==SD1_Write_Cmd(pCMD58)) //写入CMD58，开始鉴别SD2.0
   {
	  rbuf[0]=SD1_SPI_RByte(); rbuf[1]=SD1_SPI_RByte(); //读取4个字节的OCR，其中CCS指明了是SDHC还是普通的SD
	  rbuf[2]=SD1_SPI_RByte(); rbuf[3]=SD1_SPI_RByte();	

    if(rbuf[0]&0x40) 
		{
		 SD1_Ver=SD_VER_V2HC; //SDHC卡	
		 SD1_Addr_Mode=1; //SDHC卡的扇区寻址方式是扇区地址
		}	
    else SD1_Ver=SD_VER_V2; //普通的SD卡，2.0的卡包含SDHC和一些普通的卡				
   }
  }
 }
 else //SD V1.0或MMC 
 {
	//SD卡使用ACMD41进行初始化，而MMC使用CMD1来进行初始化，依此来进一步判断是SD还是MMC
	SD1_Write_Cmd(pCMD55);//写入CMD55
	r=SD1_Write_Cmd(pACMD41S);//写入ACMD41，针对SD1.0
    
  if(r<=1) //检查返回值是否正确，如果正确，说明ACMD41命令被接受，即为SD卡
  {
	 SD1_Ver=SD_VER_V1; //普通的SD1.0卡，一般来说容量不会超过2G
			
	 time=0;
	 do
	 {
		SD1_Write_Cmd(pCMD55);//写入CMD55
		r=SD1_Write_Cmd(pACMD41S);//写入ACMD41，针对SD1.0
		time++;
    if(time>=TRY_TIME) 
    { 
     return(INIT_SDV1_ACMD41_ERROR);//对SD1.0使用ACMD41进行初始化时产生错误
    }
   }while(r!=0);			 
  }
  else //否则为MMC	
	{
	 SD1_Ver=SD_VER_MMC; //MMC卡，它不支持ACMD41命令，而是使用CMD1进行初始化
			
	 time=0;
   do
   { 
    r=SD1_Write_Cmd(pCMD1);//写入CMD1
    time++;
    if(time>=TRY_TIME) 
    { 
     return(INIT_CMD1_ERROR);//MMC卡使用CMD1命令进行初始化中产生错误
    }
   }while(r!=0);			
  }
 }
 
 if(0!=SD1_Write_Cmd(pCMD16)) //SD卡的块大小必须为512字节
 {
	SD1_Ver=SD_VER_ERR; //如果不成功，则此卡为无法识别的卡
	return INIT_ERROR;
 }	
 
 SET_SD1_CS_PIN(1);
 SD1_SPI_WByte(0xFF); //按照SD卡的操作时序在这里补8个时钟 
 
 SD1_SPI_SPEED_HIGH(); //SPI切到高速
 
 return 0;//返回0,说明复位操作成功
}

/******************************************************************
 - 功能描述：对SD卡若干个扇区进行擦除，擦除后扇区中的数据大部分情况
             下为全0（有些卡擦除后为全0XFF，如要使用此函数，请确认）
 - 参数说明：addr_sta：开始扇区地址   addr_end：结束扇区地址
 - 返回说明：调用成功，返回0x00，否则返回错误码
 ******************************************************************/

UINT8 SD1_Erase_nSector(UINT32 addr_sta,UINT32 addr_end)
{
 UINT8 r,time;
// UINT8 i=0;
 UINT8 pCMD32[]={0x60,0x00,0x00,0x00,0x00,0xff}; //设置擦除的开始扇区地址
 UINT8 pCMD33[]={0x61,0x00,0x00,0x00,0x00,0xff}; //设置擦除的结束扇区地址
 UINT8 pCMD38[]={0x66,0x00,0x00,0x00,0x00,0xff}; //擦除扇区

 if(!SD1_Addr_Mode) {addr_sta<<=9;addr_end<<=9;} //addr = addr * 512	将块地址（扇区地址）转为字节地址

 pCMD32[1]=addr_sta>>24; //将开始地址写入到CMD32字节序列中
 pCMD32[2]=addr_sta>>16;
 pCMD32[3]=addr_sta>>8;
 pCMD32[4]=addr_sta;	 

 pCMD33[1]=addr_end>>24; //将开始地址写入到CMD32字节序列中
 pCMD33[2]=addr_end>>16;
 pCMD33[3]=addr_end>>8;
 pCMD33[4]=addr_end;	

 time=0;
 do
 {  
  r=SD1_Write_Cmd(pCMD32);
  time++;
  if(time==TRY_TIME) 
  { 
   return(r); //命令写入失败
  }
 }while(r!=0);  
 
 time=0;
 do
 {  
  r=SD1_Write_Cmd(pCMD33);
  time++;
  if(time==TRY_TIME) 
  { 
   return(r); //命令写入失败
  }
 }while(r!=0);  
 
 time=0;
 do
 {  
  r=SD1_Write_Cmd(pCMD38);
  time++;
  if(time==TRY_TIME) 
  { 
   return(r); //命令写入失败
  }
 }while(r!=0);

 return 0; 

}

/****************************************************************************
 - 功能描述：将buffer指向的512个字节的数据写入到SD卡的addr扇区中
 - 参数说明：addr:扇区地址
             buffer:指向数据缓冲区的指针
 - 返回说明：调用成功，返回0x00，否则返回错误码
 - 注：SD卡初始化成功后，读写扇区时，尽量将SPI速度提上来，提高效率
 ****************************************************************************/

UINT8 SD1_Write_Sector(UINT32 addr,UINT8 *buffer)	//向SD卡中的指定地址的扇区写入512个字节，使用CMD24（24号命令）
{  
 UINT8 r,time;
 UINT8 i=0;
 UINT8 pCMD24[]={0x58,0x00,0x00,0x00,0x00,0xff}; //向SD卡中单个块（512字节，一个扇区）写入数据，用CMD24

 if(!SD1_Addr_Mode) addr<<=9; //addr = addr * 512	将块地址（扇区地址）转为字节地址

 pCMD24[1]=addr>>24; //将字节地址写入到CMD24字节序列中
 pCMD24[2]=addr>>16;
 pCMD24[3]=addr>>8;
 pCMD24[4]=addr;	

 time=0;
 do
 {  
  r=SD1_Write_Cmd(pCMD24);
  time++;
  if(time==TRY_TIME) 
  { 
   return(r); //命令写入失败
  }
 }while(r!=0); 

 while(0XFF!=SD1_SPI_RByte()); //等待SD卡准备好，再向其发送命令及后续的数据
	
 SD1_SPI_WByte(0xFE);//写入开始字节 0xfe，后面就是要写入的512个字节的数据	
	
 for(i=0;i<4;i++) //将缓冲区中要写入的512个字节写入SD1卡，减少循环次数，提高数据写入速度
 {
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
 }
  
 SD1_SPI_WByte(0xFF); 
 SD1_SPI_WByte(0xFF); //两个字节的CRC校验码，不用关心
       
 r=SD1_SPI_RByte();   //读取返回值
 if((r & 0x1F)!=0x05) //如果返回值是 XXX00101 说明数据已经被SD卡接受了
 {
  return(WRITE_BLOCK_ERROR); //写块数据失败
 }
 
 while(0xFF!=SD1_SPI_RByte());//等到SD卡不忙（数据被接受以后，SD卡要将这些数据写入到自身的FLASH中，需要一个时间）
						                 //忙时，读回来的值为0x00,不忙时，为0xff

 SET_SD1_CS_PIN(1);
 SD1_SPI_WByte(0xFF); //按照SD卡的操作时序在这里补8个时钟 
 
 return(0);		 //返回0,说明写扇区操作成功
} 

/****************************************************************************
 - 功能描述：读取addr扇区的512个字节到buffer指向的数据缓冲区
 - 参数说明：addr:扇区地址
             buffer:指向数据缓冲区的指针
 - 返回说明：调用成功，返回0x00，否则返回错误码
 - 注：SD卡初始化成功后，读写扇区时，尽量将SPI速度提上来，提高效率
 ****************************************************************************/

UINT8 SD1_Read_Sector(UINT32 addr,UINT8 *buffer)//从SD卡的指定扇区中读出512个字节，使用CMD17（17号命令）
{
 UINT8 i;
 UINT8 time,r;
	
 UINT8 pCMD17[]={0x51,0x00,0x00,0x00,0x00,0x01}; //CMD17的字节序列
   
 if(!SD1_Addr_Mode) addr<<=9; //sector = sector * 512	   将块地址（扇区地址）转为字节地址

 pCMD17[1]=addr>>24; //将字节地址写入到CMD17字节序列中
 pCMD17[2]=addr>>16;
 pCMD17[3]=addr>>8;
 pCMD17[4]=addr;	

 time=0;
 do
 {  
  r=SD1_Write_Cmd(pCMD17); //写入CMD17
  time++;
  if(time==TRY_TIME) 
  {
   return(READ_BLOCK_ERROR); //读块失败
  }
 }while(r!=0); 
   			
 while(SD1_SPI_RByte()!= 0xFE); //一直读，当读到0xfe时，说明后面的是512字节的数据了

 for(i=0;i<4;i++)	 //将数据写入到数据缓冲区中
 {	
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
 }

 SD1_SPI_RByte();
 SD1_SPI_RByte();//读取两个字节的CRC校验码，不用关心它们

 SET_SD1_CS_PIN(1);
 SD1_SPI_WByte(0xFF); //按照SD1卡的操作时序在这里补8个时钟 

 return 0;
}

/****************************************************************************
 - 功能描述：向addr扇区开始的nsec个扇区写入数据（★硬件多扇区写入）
 - 参数说明：nsec:扇区数
             addr:开始扇区地址
             buffer:指向数据缓冲区的指针
 - 返回说明：调用成功，返回0x00，否则返回错误码
 - 注：SD卡初始化成功后，读写扇区时，尽量将SPI速度提上来，提高效率
 ****************************************************************************/

UINT8 SD1_Write_nSector(UINT32 nsec,UINT32 addr,UINT8 *buffer)	
{  
 UINT8 r,time;
 UINT32 i=0,j=0;
	
 UINT8 pCMD25[6]={0x59,0x00,0x00,0x00,0x00,0x01}; //CMD25用于完成多块连续写
 UINT8 pCMD55[6]={0x77,0x00,0x00,0x00,0x00,0x01}; //CMD55，用于告知SD卡后面是ACMD,CMD55+ACMD23
 UINT8 pACMD23[6]={0x57,0x00,0x00,0x00,0x00,0x01};//CMD23，多块连续预擦除

 if(!SD1_Addr_Mode) addr<<=9; 

 pCMD25[1]=addr>>24;
 pCMD25[2]=addr>>16;
 pCMD25[3]=addr>>8;
 pCMD25[4]=addr;

 pACMD23[1]=nsec>>24;
 pACMD23[2]=nsec>>16;
 pACMD23[3]=nsec>>8;
 pACMD23[4]=nsec; 

 if(SD1_Ver!=SD_VER_MMC) //如果不是MMC卡，则首先写入预擦除命令，CMD55+ACMD23，这样后面的连续块写的速度会更快
 {
	SD1_Write_Cmd(pCMD55);
	SD1_Write_Cmd(pACMD23);
 }

 time=0;
 do
 {  
  r=SD1_Write_Cmd(pCMD25);
  time++;
  if(time==TRY_TIME) 
  { 
   return(WRITE_CMD25_ERROR); //命令写入失败
  }
 }while(r!=0); 

 while(0XFF!=SD1_SPI_RByte()); //等待SD卡准备好，再向其发送命令及后续的数据

 for(j=0;j<nsec;j++)
 {
  SD1_SPI_WByte(0xFC);//写入开始字节 0xfc，后面就是要写入的512个字节的数据	
	
  for(i=0;i<4;i++) //将缓冲区中要写入的512个字节写入SD卡
  {
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
   SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));SD1_SPI_WByte(*(buffer++));
  }
  
  SD1_SPI_WByte(0xFF); 
  SD1_SPI_WByte(0xFF); //两个字节的CRC校验码，不用关心
       
  r=SD1_SPI_RByte();   //读取返回值
  if((r & 0x1F)!=0x05) //如果返回值是 XXX00DELAY_TIME1 说明数据已经被SD卡接受了
  {
   return(WRITE_NBLOCK_ERROR); //写块数据失败
  }
 
  while(0xFF!=SD1_SPI_RByte());//等到SD卡不忙（数据被接受以后，SD卡要将这些数据写入到自身的FLASH中，需要一个时间）
						                   //忙时，读回来的值为0x00,不忙时，为0xff
 }

 SD1_SPI_WByte(0xFD);

 while(0xFF!=SD1_SPI_RByte());

 SET_SD1_CS_PIN(1);//关闭片选

 SD1_SPI_WByte(0xFF);//按照SD卡的操作时序在这里补8个时钟

 return(0);		 //返回0,说明写扇区操作成功
} 

/****************************************************************************
 - 功能描述：读取addr扇区开始的nsec个扇区的数据（★硬件多扇区读取）
 - 参数说明：nsec:扇区数
             addr:开始扇区地址
             buffer:指向数据缓冲区的指针
 - 返回说明：调用成功，返回0x00，否则返回错误码
 - 注：SD卡初始化成功后，读写扇区时，尽量将SPI速度提上来，提高效率
 ****************************************************************************/

UINT8 SD_Read_nSector(UINT32 nsec,UINT32 addr,UINT8 *buffer)
{
 UINT8 r,time;
 UINT32 i=0,j=0;
	
 UINT8 pCMD18[6]={0x52,0x00,0x00,0x00,0x00,0x01}; //CMD18的字节序列
 UINT8 pCMD12[6]={0x1C,0x00,0x00,0x00,0x00,0x01}; //CMD12，强制停止命令
   
 if(!SD1_Addr_Mode) addr<<=9; //sector = sector * 512	   将块地址（扇区地址）转为字节地址,如果SD1_Addr_Mode=0则为字节寻址

 pCMD18[1]=addr>>24; //将字节地址写入到CMD17字节序列中
 pCMD18[2]=addr>>16;
 pCMD18[3]=addr>>8;
 pCMD18[4]=addr;	

 time=0;
 do
 {  
  r=SD1_Write_Cmd(pCMD18); //写入CMD18
  time++;
  if(time==TRY_TIME) 
  {
   return(READ_CMD18_ERROR); //写入CMD18失败
  }
 }while(r!=0); 
 
 for(j=0;j<nsec;j++)
 {  
  while(SD1_SPI_RByte()!= 0xFE); //一直读，当读到0xfe时，说明后面的是512字节的数据了
 
  for(i=0;i<4;i++)	 //将数据写入到数据缓冲区中
  {	
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
   *(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();*(buffer++)=SD1_SPI_RByte();
  }
 
  SD1_SPI_RByte();
  SD1_SPI_RByte();//读取两个字节的CRC校验码，不用关心它们
 }

 SD1_Write_Cmd(pCMD12); //写入CMD12命令，停止数据读取 

 SET_SD1_CS_PIN(1);
 SD1_SPI_WByte(0xFF); //按照SD卡的操作时序在这里补8个时钟 

 return 0;
}

/****************************************************************************
 - 功能描述：获取SD卡的总扇区数（通过读取SD卡的CSD寄器组计算得到总扇区数）
 - 参数说明：无
 - 返回说明：返回SD卡的总扇区数
 - 注：无
 ****************************************************************************/

UINT32 SD1_GetTotalSec(void)
{
 UINT8 pCSD[16];
 UINT32 Capacity;  
 UINT8 n,i;
 UINT16 csize; 

 UINT8 pCMD9[6]={0x49,0x00,0x00,0x00,0x00,0x01}; //CMD9	

 if(SD1_Write_Cmd(pCMD9)!=0) //写入CMD9命令
 {
	return GET_CSD_ERROR; //获取CSD时产生错误
 }

 while(SD1_SPI_RByte()!= 0xFE); //一直读，当读到0xfe时，说明后面的是16字节的CSD数据

 for(i=0;i<16;i++) pCSD[i]=SD1_SPI_RByte(); //读取CSD数据

 SD1_SPI_RByte();
 SD1_SPI_RByte(); //读取两个字节的CRC校验码，不用关心它们

 SET_SD1_CS_PIN(1);
 SD1_SPI_WByte(0xFF); //按照SD卡的操作时序在这里补8个时钟 
	
 //如果为SDHC卡，即大容量卡，按照下面方式计算
 if((pCSD[0]&0xC0)==0x40)	 //SD2.0的卡
 {	
	csize=pCSD[9]+(((UINT16)(pCSD[8]))<<8)+1;
  Capacity=((UINT32)csize)<<10;//得到扇区数	 		   
 }
 else //SD1.0的卡
 {	
	n=(pCSD[5]&0x0F)+((pCSD[10]&0x80)>>7)+((pCSD[9]&0x03)<<1)+2;
	csize=(pCSD[8]>>6)+((UINT16)pCSD[7]<<2)+((UINT16)(pCSD[6]&0x03)<<0x0A)+1;
	Capacity=(UINT32)csize<<(n-9);//得到扇区数   
 }
 return Capacity;
}



