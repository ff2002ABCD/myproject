#ifndef __JLX256128G_H
#define __JLX256128G_H

#include "main.h"
#include "stdio.h"
#define uchar unsigned char
#define uint unsigned int

void waitkey(void);
void initial_lcd(void);
void clear_screen(void);
void display_string_16x16(uchar column, uchar page,uchar *text);
void disp_16x16(int x,int y,int a);
void disp_256x128(int x,int y,char *dp);
void test(int x,int y);
void StringPrint(int x,int y,char *p);
void Characterprint(int x,int y,char *p);


#endif
