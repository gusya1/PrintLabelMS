@echo off
setlocal
rem URL zip-архива poppler с GitHub Releases этого репозитория
rem (обновить при изменении имени релиза или архива).
rem Архив должен содержать папку poppler-25.07.0/ на верхнем уровне.
set POPPLER_URL=https://github.com/gusya1/PrintLabelMS/releases/download/poppler-windows-x64-25.07.0/poppler-windows-x64-25.07.0.zip

rem Корень репозитория — родитель каталога scripts/
cd /d "%~dp0.."

if exist "build\windows\external\poppler-25.07.0\Library\bin\pdfinfo.exe" (
    echo Poppler уже установлен: build\windows\external\poppler-25.07.0
    exit /b 0
)

set ZIP=%TEMP%\poppler-windows-x64-25.07.0.zip
echo Скачивание poppler...
curl -L --fail -o "%ZIP%" "%POPPLER_URL%"
if errorlevel 1 (
    echo Не удалось скачать: %POPPLER_URL%
    echo Проверьте, что релиз и архив существуют.
    exit /b 1
)

mkdir "build\windows\external" 2>nul
echo Распаковка...
tar -xf "%ZIP%" -C "build\windows\external"
if errorlevel 1 (
    echo Не удалось распаковать архив
    del "%ZIP%"
    exit /b 1
)
del "%ZIP%"

if exist "build\windows\external\poppler-25.07.0\Library\bin\pdfinfo.exe" (
    echo Poppler установлен: build\windows\external\poppler-25.07.0
    exit /b 0
) else (
    echo pdfinfo.exe не найден после распаковки — проверьте структуру архива
    exit /b 1
)
