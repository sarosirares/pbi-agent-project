$baseUrl = "http://localhost:8000/v1"

Write-Host "Checking API..."

$models = Invoke-RestMethod -Uri "$baseUrl/models" -Method Get

$model = $models.data[0].id

Write-Host "API is available."
Write-Host "Model: $model"

$body = @{
    model = $model
    messages = @(
        @{
            role = "user"
            content = "Reply exactly with: API OK"
        }
    )
    max_tokens = 50
    chat_template_kwargs = @{
        enable_thinking = $false
    }
} | ConvertTo-Json -Depth 5

$response = Invoke-RestMethod `
    -Uri "$baseUrl/chat/completions" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "Model response:"
Write-Host $response.choices[0].message.content