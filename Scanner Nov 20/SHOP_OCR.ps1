# Local Windows OCR helper: stdin JSON path or base64 PNG object; one JSON result.
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$null = [Windows.Storage.Streams.IRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.SoftwareBitmap,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapPixelFormat,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapAlphaMode,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime]
$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethodDefinition -and
    $_.GetGenericArguments().Count -eq 1 -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.IsGenericType -and
    $_.GetParameters()[0].ParameterType.GetGenericTypeDefinition().FullName -eq 'Windows.Foundation.IAsyncOperation`1'
} | Select-Object -First 1
function Await($operation, [type]$type) {
    $task = $asTask.MakeGenericMethod($type).Invoke($null, @($operation))
    $task.Wait()
    return $task.Result
}
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new('en-US'))
if (-not $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
while ($null -ne ($inputLine = [Console]::ReadLine())) {
    $stream = $null
    $bitmap = $null
    $rawBitmap = $null
    $writer = $null
    $output = $null
    $stage = 'initialize'
    try {
        if (-not $engine) { throw 'Windows OCR language unavailable' }
        $stage = 'open PNG'
        $payload = ConvertFrom-Json -InputObject $inputLine
        if ($payload -is [string]) {
            $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($payload)) ([Windows.Storage.StorageFile])
            $stream = Await ($file.OpenReadAsync()) ([Windows.Storage.Streams.IRandomAccessStreamWithContentType,Windows.Storage.Streams,ContentType=WindowsRuntime])
        } elseif ($payload.png -is [string]) {
            $stage = 'memory PNG'
            $data = [Convert]::FromBase64String($payload.png)
            $stream = [Windows.Storage.Streams.InMemoryRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime]::new()
            $output = $stream.GetOutputStreamAt(0)
            $writer = [Windows.Storage.Streams.DataWriter,Windows.Storage.Streams,ContentType=WindowsRuntime]::new($output)
            $writer.WriteBytes($data)
            $null = Await ($writer.StoreAsync()) ([uint32])
            $null = Await ($writer.FlushAsync()) ([bool])
            $null = $writer.DetachStream()
            $writer.Dispose()
            $writer = $null
            $stream.Seek(0)
        } else { throw 'Unsupported OCR request' }
        $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $stage = 'decode PNG'
        $rawBitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        $stage = 'convert BGRA8'
        $bitmap = [Windows.Graphics.Imaging.SoftwareBitmap]::Convert($rawBitmap,[Windows.Graphics.Imaging.BitmapPixelFormat]::Bgra8,[Windows.Graphics.Imaging.BitmapAlphaMode]::Ignore)
        $stage = 'recognize'
        $result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult,Windows.Foundation,ContentType=WindowsRuntime])
        $lines = @($result.Lines | ForEach-Object {
            $words = @($_.Words)
            if ($words.Count -gt 0) {
                $rect = $words[0].BoundingRect
                @{text=$_.Text; y=($rect.Y + $rect.Height / 2)}
            }
        })
        [Console]::WriteLine((@{ok=$true;lines=$lines} | ConvertTo-Json -Compress -Depth 5))
    } catch {
        [Console]::WriteLine((@{ok=$false;error=($stage + ': ' + $_.Exception.GetBaseException().Message)} | ConvertTo-Json -Compress))
    } finally {
        if ($bitmap) { $bitmap.Dispose() }
        if ($rawBitmap) { $rawBitmap.Dispose() }
        if ($writer) { try { $writer.Dispose() } catch {} }
        if ($output) { try { $output.Dispose() } catch {} }
        if ($stream) { $stream.Dispose() }
    }
}
