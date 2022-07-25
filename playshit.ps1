Add-Type -AssemblyName presentationCore
 $file_data = Get-Content C:\automation\filename.txt
 $filepath = [uri] $file_data
 $wmplayer = New-Object System.Windows.Media.MediaPlayer
 $wmplayer.Open($filepath)
 Start-Sleep 2 # This allows the $wmplayer time to load the audio file
 $duration = $wmplayer.NaturalDuration.TimeSpan.TotalSeconds
 $wmplayer.Play()
 Start-Sleep $duration
 $wmplayer.Stop()
 $wmplayer.Close()
