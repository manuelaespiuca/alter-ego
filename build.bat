@echo off
rem Gera o app do Alter Ego em dist\AlterEgo\ (precisa do Python instalado).
rem Para ver erros do programa durante um teste, tire o --noconsole da linha do pyinstaller.

python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto erro

python -m PyInstaller main.py --onedir --noconsole --noconfirm --name AlterEgo --add-data "web;web" --collect-data eel
if errorlevel 1 goto erro

echo.
echo Pronto: dist\AlterEgo\AlterEgo.exe
echo Para mandar para alguem, compacte a pasta dist\AlterEgo em um .zip
pause
exit /b 0

:erro
echo.
echo Algo deu errado. Veja a mensagem acima.
pause
exit /b 1