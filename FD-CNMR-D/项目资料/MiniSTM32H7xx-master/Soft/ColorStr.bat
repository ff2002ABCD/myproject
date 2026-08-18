:ColorStr <attr> <sp> <"str"> <bk> <sp> <enter>
%::::       |     |     |      |    |     |            %
%::::      颜色  空格 字符串  退格 空格 回车换行       %
for %%a in (+%2 +%4 +%5 +%6) do (
   if "%%a"=="+" echo 控制参数不能为空&exit/b
   if %%a lss +0 echo 参数越界-&exit/b
   if %%a geq +a echo 参数越界+&exit/b)
if %3 == "" echo 字符串不能为空&exit/b
pushd %tmp%&setlocal ENABLEEXTENSIONS
:: 将生成的临时文件删除
if exist "%~3?" del/a/q "%~3?">nul 2>nul
if %2 gtr 0 call:ColorStr_bs %2 sp " "&call set/p=%%sp%%<nul
:: 添加退格符
if %4 gtr 0 (call:ColorStr_bs %4 bk "") else set "bk="
call:ColorStr_bs %5 sp " "
set/p=%bk%%sp%<nul>"%~3"&findstr /a:%1 .* "%~3?" 2>nul
if not %6 equ 0 for /l %%a in (1 1 %6)do echo.
endlocal&popd&goto:eof

:ColorStr_bs
set "p="&for /l %%a in (1 1 %1)do call set "p=%%p%%%~3"
set "%2=%p%"&goto:eof
