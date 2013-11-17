$VERYPDF_HOME="E:\ProgramFiles\pdf2txtocrcmd"
$CURRENT_LOC=$MyInvocation.MyCommand.Path
echo $CURRENT_LOC

$CURRENT_LOC = $CURRENT_LOC.Replace("batchrun.ps1", "")
echo $CURRENT_LOC

#$input="input"
#$output="output"
$input="ocr_test"
$output="ocr_test_out"

echo ${VERYPDF_HOME}\${input}
cd ${VERYPDF_HOME}

$starttime=Get-Date

# Run OCR for every file in the directory
foreach ($file in Get-ChildItem .\${input}) {
    echo "Processing $file"
    echo ".\pdf2txtocr.exe -ocr .\$input\$file .\$output\$file.txt"
    .\pdf2txtocr.exe -ocr .\$input\$file .\$output\$file.txt
}

$endtime=Get-Date
echo $starttime
echo $endtime
echo "TotalTime in Seconds " ($endtime-$starttime).TotalSeconds

cd $CURRENT_LOC