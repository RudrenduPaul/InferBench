Output docs/usage.gif

Set Shell "bash"
Set FontSize 16
Set Width 760
Set Height 260
Set Theme "Dracula"
Set WindowBar Colorful
Set WindowBarSize 36
Set Padding 20

Type "export PS1='$ '"
Enter
Sleep 300ms

Type "python3 -m venv .venv && source .venv/bin/activate"
Enter
Sleep 2s

Type "pip install inferbench-cli"
Enter
Sleep 3s

Type "inferbench run --engines omlx --model qwen2.5-1.5b-instruct-4bit --max-tokens 40 --json --out report.json"
Enter
Sleep 15s

Type "ls report.json"
Enter
Sleep 1s
