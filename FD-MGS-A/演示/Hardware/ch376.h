#ifndef __CH376_H
#define __CH376_H
#include "stdint.h"
#include "CH376INC.H"

#define ERR_USB_UNKNOWN  0xFA
uint8_t file_writeData(char* buf);
uint8_t CH376_TestConnection(void);
void CH376_Init(void);
void xWriteCH376Cmd( unsigned char cmd );
void xWriteCH376Data( unsigned char dat );
unsigned char xReadCH376Data(void);
void xEndCH376Cmd(void);
unsigned char	Query376Interrupt( void );		/* ???CH376?��?(INT#?????????) */
void ch376_init(void);
void ch376_writetest(void);
uint8_t CH376_SetBaudrate(void);  // ����CH376������Ϊ115200�ĺ���
uint8_t ch376_init_with_baudrate_change(void);  // ���������л��ĳ�ʼ������������1=�ɹ���0=ʧ��
uint8_t ch376_read_calibration(void);  // ��ȡCALIBO�ļ��еı궨ϵ������
uint8_t ch376_export_calibration(void); // �����궨ϵ����CALIBO.TXT�ļ�����
#endif
