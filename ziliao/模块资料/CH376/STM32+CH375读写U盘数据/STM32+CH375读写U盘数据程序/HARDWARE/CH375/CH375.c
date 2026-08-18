/*******************************************************************************
* CopyRight   : 
* File        : CH375.c
* Author      :
* Date        : 
* Description : CH375 基本操作函数 
* Version     :
*******************************************************************************/

/* Includes --------------------------------------------------*/
#include"CH375.h"

/* Variables ------------------------------------------------*/
uint8_t BlockPerSector;  //每扇区数据块数
uint32_t BytePerSector;  //每扇区字节数
uint8_t DATA_BUFFER[8];  //数据缓冲区

/* Functions ------------------------------------------------*/
/******************************************************************************
* Function    ： CH375_DelayNus
* Description :  延时函数
* Input       :  nCount
* Output      ： None
* Return      ： None
*******************************************************************************/
void CH375_DelayNus(__IO uint32_t nCount)
{
    uint32_t i;
    for(i=nCount;i!=0;i--);
}

/*******************************************************************************
* Funtion     : CH375_Configuration
* Description : CH375 对应时钟，引脚的配置
* Input       : None 
* Output      : None 
* Return      :  
*******************************************************************************/
void CH375_Configuration(void)
{
    /* 使能 CH375 引脚时钟-------------------------------------*/
//    SystemInit();
	GPIO_InitTypeDef GPIO_InitStructure;
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIO_CH375_Data | 
                           RCC_APB2Periph_GPIO_CH375_CTL |
							RCC_APB2Periph_GPIO_CH375_INT , ENABLE);
    
    /* CH375 控制引脚配置--------------------------------------*/ 
    
    
    /* 中断输入脚 INT# PB1 */
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_1 ;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING ;
    GPIO_Init(GPIOB,&GPIO_InitStructure);
    
    /* A0 , CS# , RD#, WR# 测试*/
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_4 | GPIO_Pin_5 | GPIO_Pin_6 
                                 | GPIO_Pin_7 ;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP ;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA,&GPIO_InitStructure);
}

/*******************************************************************************
* Funtion     : CH375_WriteCmd
* Description : 向CH375写入命令 
* Input       : 命令 cmd 
* Output      : None 
* Return      :  
*******************************************************************************/
void CH375_WriteCmd(uint8_t cmd)
{
    uint16_t  TempData = 0 ;
    
    DATA_MODE_OUT;                // 输出模式
    
    //CS_L ;                      // 打开CH375  
   
    TempData = GPIO_ReadOutputData(GPIO_CH375_Data);
    TempData &= 0xFF00;
    TempData |= (uint16_t)cmd ;    // 8位的命令强制转换为16位（高8位都为0） 
    CH375_DelayNus(100);
    GPIO_Write(GPIO_CH375_Data, TempData);   // 写入命令 
    
    A0_H ;                      // 命令模式
    
    RD_H;                       // 读选通关闭
    // CH375_DelayNus_Nus(50);
    WR_L;                       // 写选通打开 
    // CH375_DelayNus_Nus(100);
    
    WR_H;                       // 写选通关闭 
    // CH375_DelayNus_Nus(50);
    //CS_H;                       // 关闭片选  
    A0_L; 
    //CH375_DelayNus_Nus(100);   
}

/*******************************************************************************
* Funtion     : CH375_WriteData
* Description : 向CH375写入数据 
* Input       : 数据 data  
* Output      : None 
* Return      :  
*******************************************************************************/
void CH375_WriteDat(uint8_t dat)
{
    uint16_t  TempData;
    
    DATA_MODE_OUT;                // 输出模式
    
    //CS_L ;                        // 打开CH375 
    
    TempData = GPIO_ReadOutputData(GPIO_CH375_Data);
    TempData &= 0xFF00;
    TempData |= (uint16_t)dat ;    // 8位的数据强制转换为16位（高8位都为0） 
    CH375_DelayNus(100);
    GPIO_Write(GPIO_CH375_Data, TempData);   // 写入数据 
    
    A0_L ;                        // 数据模式 
    RD_H ;                          // 读选通关闭 
    //CH375_DelayNus(50); 
    WR_L ;                          // 写选通打开
    //CH375_DelayNus(150);
    
    WR_H;                         // 写选通关闭 
    // CH375_DelayNus( 50 );
    //CS_H;                         // 关闭片选  
    A0_L;                         // A0 恢复为1  ？？？？？
    // CH375_DelayNus_Nus( 100 );	 
} 

/*******************************************************************************
* Funtion     : CH375_ReadCmd
* Description : 从CH375读到命令 
* Input       : None 
* Output      :  
* Return      : 读到的命令cmd 
*******************************************************************************/
uint8_t CH375_ReadCmd(void)
{
    uint8_t PortData; 
	 
    DATA_MODE_IN;             // 输入模式 
    //CS_L ;                    // 打开片选 
    A0_H ;                    // 命令模式
    
    WR_H ;                    // 写选通关闭 
    //CH375_DelayNus( 50 );
    RD_L ;                    // 读选通打开 
    //CH375_DelayNus( 25 );
    PortData=(uint8_t)(GPIO_ReadInputData(GPIO_CH375_Data));
    //CH375_DelayNus( 25 );
    RD_H;
    //CH375_DelayNus(50);
    //CS_H;
    A0_L;           // ????????????????????????????????????
    //CH375_DelayNus(500);
    return PortData;

}
/*******************************************************************************
* Funtion     : CH375_ReadData
* Description : 从CH375读到数据 
* Input       : None 
* Output      :  
* Return      : 读到的数据data 
*******************************************************************************/
uint8_t  CH375_ReadDat(void)
{
    uint8_t PortData; 
	 
    DATA_MODE_IN;             // 输入模式 
    //CS_L ;                    // 打开片选 
    A0_L ;                    // 读取数据 
    WR_H ;                    // 写选通关闭 
    //CH375_DelayNus( 50 );
    RD_L ;                    // 读选通打开 
    //CH375_DelayNus( 25 );
    PortData=(uint8_t)(GPIO_ReadInputData(GPIO_CH375_Data));
    //CH375_DelayNus( 25 );
    RD_H;
    //CH375_DelayNus( 50 );
    //CS_H;
    A0_H;
    //CH375_DelayNus( 50 );
    return PortData;
}

/*******************************************************************************
* Funtion     : CH375_Wait_Interrupt
* Description : 等待中断信号，即INT引脚上产生低电平，并获取中断状态码，获取后INT恢复高电平，以产生下一次中断信号 
* Input       : None 
* Output      :  
* Return      : 返回中断状态 
*******************************************************************************/
uint8_t CH375_WaitInterrupt(void)  
{    
    //CH375_DelayNus_Nus( 500 );
    while( GPIO_ReadInputDataBit(GPIO_CH375_INT, GPIO_Pin_1) );  /* 查询等待CH375操作完成中断(INT#低电平) */
    CH375_WriteCmd( CMD_GET_STATUS );  /* 写入命令，产生操作完成中断, 获取中断状态 */
    return( CH375_ReadDat( ) );
}

/*******************************************************************************
* Funtion     : CH375_Init
* Description : CH375芯片初始化：测试CH375的工作状态、设置其为USB主机方式 
* Input       : None 
* Output      :  
* Return      : 初始化成功返回0，失败返回1 
*******************************************************************************/
uint8_t  CH375_Init(void)
{    
    uint8_t  c, i ;
    
    CS_L;
    RD_H;
    WR_H;
        
    CH375_WriteCmd(CMD_CHECK_EXIST);  /* 测试工作状态 */
    CH375_WriteDat( 0x55 );             /* 测试数据 */
    c = CH375_ReadDat( );               /* 返回数据应该是测试数据取反 */
    if ( c != 0xaa ) 
    {  
		/* CH375出错,进行重试 */
        for ( i = 100; i != 0; i -- )
        {  
            /* 强制数据同步 */
	    	CH375_WriteCmd( CMD_RESET_ALL );   /* CH375执行硬件复位 */
            CH375_DelayNus( 3200000 );         /* 延时至少30mS */
            CH375_WriteCmd( CMD_CHECK_EXIST ); /* 测试工作状态 */
            CH375_WriteDat( 0x55 );            /* 测试数据 */
            c = CH375_ReadDat( );              /* 返回数据应该是测试数据取反 */
            if ( c == 0xaa )
                break;                          /*工作正常，跳出循环 */
      }
      
    }

    CH375_WriteCmd( CMD_SET_USB_MODE );  /* 写入命令，设置其为USB工作模式 */
    CH375_WriteDat( 6 );                 /* 模式代码,自动检测USB设备连接 */
    for ( i = 0xff; i != 0; i -- )  /* 等待操作成功,通常需要等待10uS-20uS */
    {	
        CH375_DelayNus( 150 );
        if ( CH375_ReadDat( ) == CMD_RET_SUCCESS )   // 输出操作状态（数据）
	    	break;  /* 操作成功 ，跳出循环，往下执行*/
    }
    if ( i != 0 ) 
	    return( 0 );  /* 操作成功，返回0 */
    else 
	    return( 0xff );  /* CH375出错,例如芯片型号错或者处于串口方式或者不支持 */
}

/*******************************************************************************
* Funtion     : CH375_Disk_Connect
* Description : 检测设备是够连接-
* Input       : None 
* Output      :  
* Return      : 磁盘连接：返回0 ;   断开：返回断开状态
*******************************************************************************/
uint8_t CH375_DiskConnect(void)
{
    uint8_t INTStatus ;
    INTStatus = CH375_WaitInterrupt(); //等待USB设备插入连接，返回中断状态
   
    return (INTStatus);    //返回中断状态              
}


/*******************************************************************************
* Funtion     : CH375_Disk_Init
* Description : 初始化磁盘， 在使用U盘之前，先要调用此函数，此函数将进行判断
                磁盘是否连接，初始化是否成功等操作

* Input       : None 
* Output      :  
* Return      : 初始化成功返回0，失败返回1 
*******************************************************************************/
uint8_t CH375_DiskInit(void)
{
    uint8_t INTStatus, i ;
//	u32 a,b;
    
    CH375_Init();//先初始化CH375芯片
    CH375_DiskConnect();               // 检测磁盘是否连接
    
    
    CH375_WriteCmd(CMD_DISK_INIT);     // 初始化USB存储器
    INTStatus = CH375_WaitInterrupt(); // 等待中断并获取中断状态   
    if (INTStatus != USB_INT_SUCCESS) 
    {
        return (INTStatus);             // 出现错误
    }
    
    CH375_WriteCmd(CMD_DISK_SIZE);     // 获取存储器的容量
    INTStatus = CH375_WaitInterrupt(); // 获取中断状态  
    if(INTStatus != USB_INT_SUCCESS)
    { 
        CH375_DelayNus(320000);              // 出错重试
        CH375_WriteCmd(CMD_DISK_SIZE);  
        INTStatus = CH375_WaitInterrupt(); // 获取中断状态  
    }
    if(INTStatus != USB_INT_SUCCESS)
    {
        return (INTStatus);            // 整个上面的初始化 出现错误
    }
    
    /* 可以由CMD_RD_USB_DATA命令将容量数据读出,分析每扇区字节数 */
    CH375_WriteCmd( CMD_RD_USB_DATA );  /* 从CH375缓冲区（64字节）读取数据块 ,该命令返回数据块长度*/
    i = CH375_ReadDat( );                 /* 后续数据的长度 */ // 64字节分几次读完？？？？？？？？
    if ( i != 8 )                        //   ？？？？？？？？？？
    {
        return( USB_INT_DISK_ERR );  /* 异常 */
    }
    for ( i = 0; i != 8; i ++ )               // 根据长度读取数据，？？？？？？？？？？？？？
    {  
        /* 根据长度读取数据 */
	DATA_BUFFER[ i ] = CH375_ReadDat( );  /* 读出数据并保存 */
    }
    i = DATA_BUFFER[ 6 ];    /* U盘容量数据中的每扇区字节数,大端格式 */
    if ( i == 0x04 ) 
    {
        BlockPerSector = 1024/CH375_BLOCK_SIZE;  /* 磁盘的物理扇区是1K字节 */
    }
    else if ( i == 0x08 ) 
    {
        BlockPerSector = 2048/CH375_BLOCK_SIZE;  /* 磁盘的物理扇区是2K字节 */
    }
    else if ( i == 0x10 ) 
    {
        BlockPerSector = 4096/CH375_BLOCK_SIZE;  /* 磁盘的物理扇区是4K字节 */
    }
    else 
    {
        BlockPerSector = 512/CH375_BLOCK_SIZE;  /* 默认的磁盘的物理扇区是512字节 */
    }
    BytePerSector = BlockPerSector*CH375_BLOCK_SIZE;  /* 物理磁盘的扇区大小 */
//	a=(DATA_BUFFER[7]<<24)+(DATA_BUFFER[6]<<16)+(DATA_BUFFER[5]<<8)+(DATA_BUFFER[4]<<0);
//	b=(DATA_BUFFER[3]<<24)+(DATA_BUFFER[2]<<16)+(DATA_BUFFER[1]<<8)+(DATA_BUFFER[0]<<0);
//	printf("%d   \r\n",a*b);
    CH375_WriteCmd( CMD_SET_PKT_P_SEC );      /* 设置USB存储器的每扇区数据包总数 */
    CH375_WriteDat( 0x39 );
    CH375_WriteDat( BlockPerSector );  /* 设置每扇区数据包总数 */
    return( 0 );  /* U盘已经成功初始化 */      
}

/*******************************************************************************
* Funtion     : CH375_DiskReady
* Description : 检测USB设备是否准备好(USB设备已经被初始化，即已经得到分配地址)
* Input       : None 
* Output      :  
* Return      : 中断状态
*******************************************************************************/
uint8_t   CH375_DiskReady( void )
{
    CH375_WriteCmd( CMD_DISK_READY );  //写入命令
    return (CH375_WaitInterrupt());    //返回中断状态
}

/*******************************************************************************
* Funtion     : CH375_Write_Sector
* Description : 向U盘一扇区写入数据
* Input       : None 
* Output      :  
* Return      : 写入成功返回0，失败返回中断状态
*******************************************************************************/

uint8_t CH375_WriteSector(uint32_t addr , const uint8_t *pbuff)
{
    uint8_t i,j;
    uint8_t status;
    CH375_WriteCmd(CMD_DISK_WRITE); // 磁盘写命令
    
    CH375_WriteDat(addr);          // 送入32位的扇区地址，先送低位，再送高位
    CH375_WriteDat(addr >> 8);
    CH375_WriteDat(addr >> 16);
    CH375_WriteDat(addr >> 24);
    
    CH375_WriteDat(1);                 	//送入扇区数：1个扇区
    for(i = 0; i < 8; i++)  // 8次写入，一次写入64字节（主机缓冲区的大小64字节）
    {
        status = CH375_WaitInterrupt();
	if(status  == USB_INT_DISK_WRITE)      //usb设备写操作,如果扇区的数据没有写完，则继续
	{
	    CH375_WriteCmd(CMD_WR_USB_DATA7); //向USB主机端点的发送缓冲区写入数据块
	    CH375_WriteDat(64);	       //先写入的是数据的长度（多少字节）
	    for(j = 0; j < 64; j++)	       //把随后pbuf中的数据写入CH375缓冲区（64个字节）
	    {
		CH375_WriteDat(*pbuff);
		pbuff++;
	    }
	    CH375_WriteCmd(CMD_DISK_WR_GO);    // 继续写操作
	}
	else
	{
	    return status;
	}
	}
    
	status = CH375_WaitInterrupt();
	if(status == USB_INT_SUCCESS)	//如果状态码为USB_INT_SUCCESS，说明写扇区成功，返回0
	{
	 	return 0;	
	}
	else
	{
	 	return (status);
	}
}

/*******************************************************************************
* Funtion     : CH375_ReadSector
* Description : 从U盘一扇区读出数据，放到缓冲区中
* Input       : None 
* Output      :  
* Return      : 读取成功返回0，读取失败返回中断状态
*******************************************************************************/
uint8_t CH375_ReadSector(uint32_t addr, uint8_t *pbuff)
{
    uint8_t   mIntStatus;	
    uint8_t   mBlockCount;
    uint8_t   mLength;
    
    //从USB存储器读数据块:要输入扇区地址和扇区数 
    CH375_WriteCmd( CMD_DISK_READ );  /* 从USB存储器读数据块*/ 
    
    CH375_WriteDat( (u8)addr );            /* LBA的最低8位 */
    CH375_WriteDat( (u8)( addr >> 8 ) );
    CH375_WriteDat( (u8)( addr >> 16 ) );
    CH375_WriteDat( (u8)( addr >> 24 ) );  /* LBA的最高8位 */
    
    CH375_WriteDat( 1 );  /* 扇区数 */
    
    //CH375的数据缓冲区为64字节，所以读取一个扇区要读8次
    for ( mBlockCount = 8; mBlockCount != 0; mBlockCount -- )  /* 数据块计数 */
    { 
	mIntStatus = CH375_WaitInterrupt( );  /* 等待中断并获取状态 */
	if ( mIntStatus == USB_INT_DISK_READ )  /* USB存储器读数据块,请求数据读出 */
        {  
	    CH375_WriteCmd( CMD_RD_USB_DATA );  /* 从CH375缓冲区读取数据块 */
	    mLength = CH375_ReadDat( );  /* 先读到后续数据的长度 */ //先读出的是数据块的长度（1个数据块有几个字节）
	    while ( mLength )           /* 根据长度读取数据 */
            {  
		*pbuff = CH375_ReadDat( );  /* 读出数据并保存 */
		pbuff ++;
		mLength --;
	    }
	    CH375_WriteCmd( CMD_DISK_RD_GO );  /* 继续执行USB存储器的读操作 */
        }
	else 
            break;  /* 返回错误状态 */
    }
    
   mIntStatus = CH375_WaitInterrupt( );  /* 等待中断并获取状态 */
   if ( mIntStatus == USB_INT_SUCCESS ) 
   {
       return( 0 );  /* 操作成功 */
   }
   else
   {
      if(mIntStatus == USB_INT_DISK_ERR )
      {
          CH375_DelayNus(2000);
          CH375_WriteCmd(CMD_DISK_R_SENSE); /* 获取USB存储器的容量 */
          mIntStatus = CH375_WaitInterrupt();                 /* 等待中断并获取状态 */
          if(mIntStatus!=USB_INT_SUCCESS)            /* 出现错误 */
          {
              return mIntStatus;
          }
      }
      return mIntStatus;

   }
  
}
