param(
  [Parameter(Mandatory=$true)][string]$Prompt,
  [string]$Name="generated-app"
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
$root = Join-Path $here ".."
cd $root
python -m orchestrator.graph --prompt "$Prompt" --name "$Name" --out "$($root)\generated"