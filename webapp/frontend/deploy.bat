@echo off
set "PATH=%PATH%;C:\Program Files\nodejs\"
echo Deploying to Vercel with a professional name...
call npx vercel --name nhis-tracker-v2 --token "<YOUR_VERCEL_TOKEN>" --prod --yes > vercel_output.txt 2>&1
echo Done!
