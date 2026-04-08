#include"CH376INC.H"
#include "sys.h"
#define	CH376_SPI_SDI			PBout(5)     /* PB5复用      SDI   */
#define	CH376_SPI_SDO			PBout(4)     /* PB4复用      SDO   */
#define	CH376_SPI_SCK			PBout(3)	    /* PA3复用      SCK   */
#define  CH376_SPI_SCS			PDout(2)     /* PD2推挽输出  CS       */
#define  CH376_RST            PCout(11)     /* PC11推挽输出  RST   */
#define	CH376_INT_WIRE      	PCin(12)      /* PC12上拉输入  INT   */
/* 附加的USB操作状态定义 */
#define		ERR_USB_UNKNOWN		0xFA	                                                /* 未知错误,不应该发生的情况,需检查硬件或者程序错误 */


void 	mDelayuS( UINT8 us );
void	mDelay0_5uS( void );
void 	mDelaymS( UINT8 ms );
void 	CH376_PORT_INIT( void );  		                                                /* CH376通讯接口初始化 */
void	xEndCH376Cmd( void );															/* 结束SPI命令 */
//void 	xWriteCH376Cmd( UINT8 mCmd );	                                                /* 向CH376写命令 */
//void 	xWriteCH376Data( UINT8 mData );	                                                /* 向CH376写数据 */
u8 	xReadCH376Data( void );			                                                /* 从CH376读数据 */
u8 	Query376Interrupt( void );		                                                /* 查询CH376中断(INT#引脚为低电平) */
u8 	mInitCH376Host( void );			                                                /* 初始化CH376 */
						  	    													  
//void SPIx_Init(void);			 //初始化SPI口  
u8 SPIx_ReadWriteByte(u8 TxData);//SPI总线读写一个字节


