# Test Worker End-to-End
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "TEST: Worker End-to-End - Crear Design y Verificar Processing" -ForegroundColor Yellow
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Login
Write-Host "1. Autenticando..." -ForegroundColor Cyan
$loginBody = @{
    email = "test@worker.com"
    password = "Test1234!"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" `
        -Method POST `
        -Body $loginBody `
        -ContentType "application/json" `
        -UseBasicParsing
    
    $token = ($response.Content | ConvertFrom-Json).access_token
    Write-Host "   ✅ Token obtenido" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Error de login. Registrando usuario..." -ForegroundColor Yellow
    
    $registerBody = @{
        email = "test@worker.com"
        password = "Test1234!"
        full_name = "Worker Test"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/register" `
        -Method POST `
        -Body $registerBody `
        -ContentType "application/json" `
        -UseBasicParsing
    
    # Re-intentar login
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" `
        -Method POST `
        -Body $loginBody `
        -ContentType "application/json" `
        -UseBasicParsing
    
    $token = ($response.Content | ConvertFrom-Json).access_token
    Write-Host "   ✅ Usuario registrado y token obtenido" -ForegroundColor Green
}

Write-Host ""

# 2. Crear Design
Write-Host "2. Creando design..." -ForegroundColor Cyan
$designBody = @{
    product_type = "t-shirt"
    design_data = @{
        text = "Worker Test " + (Get-Date -Format "HH:mm:ss")
        font = "Bebas-Bold"
        color = "#FF0000"
        fontSize = 48
    }
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/designs" `
    -Method POST `
    -Headers @{Authorization="Bearer $token"} `
    -ContentType "application/json" `
    -Body $designBody `
    -UseBasicParsing

$design = $response.Content | ConvertFrom-Json
$designId = $design.id

Write-Host "   ✅ Design creado" -ForegroundColor Green
Write-Host "      ID: $designId"
Write-Host "      Status inicial: $($design.status)"
Write-Host ""

# 3. Esperar processing
Write-Host "3. Esperando worker processing..." -ForegroundColor Cyan
for ($i = 1; $i -le 5; $i++) {
    Write-Host "   $i..." -NoNewline
    Start-Sleep -Seconds 1
}
Write-Host " OK" -ForegroundColor Green
Write-Host ""

# 4. Verificar resultado
Write-Host "4. Verificando resultado..." -ForegroundColor Cyan
$response2 = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/designs/$designId" `
    -Headers @{Authorization="Bearer $token"} `
    -UseBasicParsing

$designUpdated = $response2.Content | ConvertFrom-Json

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "RESULTADO:" -ForegroundColor Yellow
Write-Host "=====================================================================" -ForegroundColor Cyan

Write-Host "Status: " -NoNewline
switch ($designUpdated.status) {
    "published" { Write-Host "PUBLISHED ✅" -ForegroundColor Green }
    "failed" { Write-Host "FAILED ❌" -ForegroundColor Red }
    "rendering" { Write-Host "RENDERING ⏳" -ForegroundColor Yellow }
    "draft" { Write-Host "DRAFT ⚠️" -ForegroundColor Yellow }
    default { Write-Host "$($designUpdated.status)" -ForegroundColor Gray }
}

Write-Host "Preview URL: $($designUpdated.preview_url)"
Write-Host "Thumbnail URL: $($designUpdated.thumbnail_url)"
Write-Host ""

# 5. Diagnóstico
if ($designUpdated.status -eq "published") {
    Write-Host "🎉 ¡ÉXITO TOTAL!" -ForegroundColor Green
    Write-Host ""
    Write-Host "✅ Worker procesó correctamente la tarea" -ForegroundColor Green
    Write-Host "✅ Design cambió de 'draft' → 'published'" -ForegroundColor Green
    Write-Host "✅ Preview URL generado" -ForegroundColor Green
    Write-Host "✅ Thumbnail URL generado" -ForegroundColor Green
    Write-Host ""
    Write-Host "URLs generados:" -ForegroundColor Cyan
    Write-Host "   Preview: $($designUpdated.preview_url)"
    Write-Host "   Thumbnail: $($designUpdated.thumbnail_url)"
} elseif ($designUpdated.status -eq "failed") {
    Write-Host "❌ Worker procesó pero falló durante ejecución" -ForegroundColor Red
    Write-Host ""
    Write-Host "Ver logs del worker para detalles del error:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs worker --tail 100 | Select-String -Pattern 'ERROR|Exception|Traceback'" -ForegroundColor Gray
} else {
    Write-Host "⚠️  Worker NO procesó la tarea (o aún está procesando)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Comandos de diagnóstico:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Ver logs del worker (errores):" -ForegroundColor Cyan
    Write-Host "   docker-compose logs worker --tail 50" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Verificar colas Redis:" -ForegroundColor Cyan
    Write-Host "   docker-compose exec redis redis-cli LLEN high_priority" -ForegroundColor Gray
    Write-Host "   docker-compose exec redis redis-cli LLEN default" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Verificar tareas registradas:" -ForegroundColor Cyan
    Write-Host "   docker-compose exec worker celery -A app.infrastructure.workers.celery_app inspect registered" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. Ver tareas activas:" -ForegroundColor Cyan
    Write-Host "   docker-compose exec worker celery -A app.infrastructure.workers.celery_app inspect active" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""
