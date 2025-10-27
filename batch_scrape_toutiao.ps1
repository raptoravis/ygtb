# .\batch_scrape_toutiao.ps1 -force $False -scrape_web $True
param (
	[bool]$force = $false,
	[bool]$nocache = $false,
	[bool]$scrape_web = $false,
	[bool]$scrape_app = $false,
	[bool]$all = $false,
	[int]$checks = 0,
	[int]$max = 0,
	# [string]$filepath = ".torextrader\web_toutiao_config.json"
	$source=".torextrader\toutiao",
	$target="E:\downloads\weiyun\disk\latest\life\__favreads\资治通鉴",
	$target2="D:\dev\zhuyong.git\articles",
	$original_path="D:\dev\ygtb.git" 
)

Write-Output "source=$($source) target=$($target) target2=$($target2)"
Write-Output "scrape_web=$($scrape_web) scrape_app=$($scrape_app) force=$($force) all=$($all) nocache=$($nocache) checks=$($checks) max=$($max)`n"

# $jsonData = Get-Content -Path $filepath | ConvertFrom-Json

# $items = $jsonData.items

# $num_items = $items.Length
		

$scrape_web_opt = ""
if ($scrape_web) {
	$scrape_web_opt = "--scrape"
}

$nocache_opt = ""
if ($nocache) {
	$nocache_opt = "--nocache"
}

$force_opt = ""
if ($force) {
	$force_opt = "--force"
}
$all_opt = ""
if ($all) {
	$all_opt = "--all"
}
$checks_opt = ""
if ($checks -gt 0) {
	$checks_opt = "--checks $($checks)"
}
$max_opt = ""
if ($max -gt 0) {
	$max_opt = "--checks $($max)"
}

Invoke-Expression "uv run python .\scrape\web_toutiao.py $scrape_web_opt $nocache_opt $force_opt $all_opt $checks_opt $max_opt"

 
enum SyncMode {
    CopyOnly      = 1
    CopyDelete    = 2
    CopyBothWays  = 3
}
 
function Sync-Folders () {
	param (
		[string]$source,
		[string]$target
	)
	# $sourceFiles=@(Get-ChildItem -Path $source -Recurse|ForEach-Object {$_.FullName.Remove(0,$source.Length)})
	# $targetFiles=@(Get-ChildItem -Path $target -Recurse | ForEach-Object {$_.FullName.Remove(0,$target.Length)})
	$sourceFiles=Get-ChildItem -Path $source -File
	$targetFiles=Get-ChildItem -Path $target
	
	try{
		$diff=Compare-Object -ReferenceObject $sourceFiles -DifferenceObject $targetFiles
	
		foreach($f in $diff) 
		{
			$copyParams = @{
				'Path' = $f.InputObject.FullName
			}

			if($f.SideIndicator -eq "<=") {
				$copyParams.Destination = $target
	
				Write-Host "Copying: $($copyParams.Path) To     : $($copyParams.Destination)"
				Copy-Item @copyParams
			}
		}
	}      
	catch {
		Write-Error -Message "something bad happened!`n$($Error.Item(0).Message)" -ErrorAction Stop
	}
}

$scrape_appium = $False

if ($scrape_appium) 
{
	$scrape_app_opt = ""
	if ($scrape_app) {
		$scrape_app_opt = "-s"
	}

	for ($i=1;$i -le 7;$i++) { 
		Invoke-Expression "uv run python .\scrape\appium_toutiaoapp.py -e $scrape_app_opt -d $i"
	}

	for ($i=1;$i -le 3;$i++) {
		Invoke-Expression "uv run python .\scrape\whisper.py -e $scrape_app_opt -d $i"
	}
}

# Sync-Folders $source $target
# Sync-Folders $source $target2

robocopy $source $target /mir /xd article_* w_* mp3_* txt_*
robocopy $source $target2 /mir /xd article_* w_* mp3_* txt_*

##
Write-Host "git add and push"
Set-Location $target2

git add --all
git commit -am "update"
git push

##
Set-Location $original_path
