# Test Worker - Paso a Paso
# Ejecuta cada sección y verifica los resultados

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "TEST 1: Verificar Worker Ready" -ForegroundColor Yellow
Write-Host ("=" * 80) -ForegroundColor Cyan

docker-compose exec worker celery -A app.infrastructure.workers.celery_app inspect registered
Write-Host ""
Write-Host "✅ Esperado: 3 tareas (debug_task, render_design_preview, send_email)" -ForegroundColor Green
Write-Host ""

# Pausa
Read-Host "Presiona ENTER para continuar con TEST 2"

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "TEST 2: Debug Task Directo" -ForegroundColor Yellow
Write-Host ("=" * 80) -ForegroundColor Cyan

docker-compose exec api python -c @"
from app.infrastructure.workers.celery_app import debug_task
result = debug_task.delay()
print(f'Task ID: {result.id}')
import time
time.sleep(2)
print(f'Result: {result.get(timeout=5)}')
"@

Write-Host ""
Write-Host "✅ Esperado: {'status': 'ok', 'message': 'Celery is working!'}" -ForegroundColor Green
Write-Host ""

# Pausa
Read-Host "Presiona ENTER para continuar con TEST 3"

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "TEST 3: Render Task Directo (Bypass API)" -ForegroundColor Yellow
Write-Host ("=" * 80) -ForegroundColor Cyan

docker-compose exec api python -c @"
from app.infrastructure.workers.tasks.render_design import render_design_preview
import uuid

# Crear design ID fake para test
test_design_id = str(uuid.uuid4())
print(f'Test Design ID: {test_design_id}')

# Enviar tarea
result = render_design_preview.apply_async(
    args=[test_design_id],
    queue='high_priority'
)
print(f'Task ID: {result.id}')
print(f'Queue: high_priority')
print('Esperando resultado...')

import time
time.sleep(5)

try:
    output = result.get(timeout=10)
    print(f'Result: {output}')
except Exception as e:
    print(f'Error: {e}')
"@

Write-Host ""
Write-Host "⚠️  Esperado: Falla porque design_id no existe en DB (eso es OK para test)" -ForegroundColor Yellow
Write-Host "✅ Importante: Que el worker INTENTE procesar la tarea" -ForegroundColor Green
Write-Host ""

# Pausa
Read-Host "Presiona ENTER para continuar con TEST 4"

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "TEST 4: Crear Design REAL via API" -ForegroundColor Yellow
Write-Host ("=" * 80) -ForegroundColor Cyan

Write-Host "1. Necesitas TOKEN de autenticación" -ForegroundColor Cyan
Write-Host "   Si no tienes, ejecuta primero:" -ForegroundColor Gray
Write-Host '   $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" `' -ForegroundColor Gray
Write-Host '     -Method POST -ContentType "application/json" `' -ForegroundColor Gray
Write-Host '     -Body ''{"email":"test@test.com","password":"Test1234!"}''' -ForegroundColor Gray
Write-Host '   $token = ($response.Content | ConvertFrom-Json).access_token' -ForegroundColor Gray
Write-Host ""

$executeTest4 = Read-Host "¿Tienes un TOKEN y quieres ejecutar TEST 4? (y/N)"

if ($executeTest4 -eq 'y' -or $executeTest4 -eq 'Y') {
    $token = Read-Host "Ingresa tu TOKEN"
    
    Write-Host ""
    Write-Host "Creando design..." -ForegroundColor Cyan
    
    $designBody = @{
        product_type = "t-shirt"
        design_data = @{
            text = "Worker Test"
            font = "Bebas-Bold"
            color = "#FF0000"
            fontSize = 48
        }
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/designs" `
        -Method POST `
        -Headers @{Authorization="Bearer $token"} `
        -ContentType "application/json" `
        -Body $designBody
    
    $design = $response.Content | ConvertFrom-Json
    $designId = $design.id
    
    Write-Host ""
    Write-Host "✅ Design creado:" -ForegroundColor Green
    Write-Host "   ID: $designId"
    Write-Host "   Status: $($design.status) (debe ser 'draft')"
    Write-Host ""
    
    Write-Host "Esperando 3 segundos para que worker procese..." -ForegroundColor Cyan
    Start-Sleep -Seconds 3
    
    Write-Host ""
    Write-Host "Verificando status..." -ForegroundColor Cyan
    $response2 = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/designs/$designId" `
        -Headers @{Authorization="Bearer $token"}
    
    $designUpdated = $response2.Content | ConvertFrom-Json
    
    Write-Host ""
    Write-Host "📊 Resultado Final:" -ForegroundColor Yellow
    Write-Host "   Status: $($designUpdated.status)" -ForegroundColor $(if ($designUpdated.status -eq "published") { "Green" } else { "Red" })
    Write-Host "   Preview URL: $($designUpdated.preview_url)"
    Write-Host "   Thumbnail URL: $($designUpdated.thumbnail_url)"
    Write-Host ""
    
    if ($designUpdated.status -eq "published") {
        Write-Host "🎉 ¡ÉXITO! Worker procesó correctamente" -ForegroundColor Green
    } else {
        Write-Host "❌ Worker NO procesó. Status sigue en '$($designUpdated.status)'" -ForegroundColor Red
        Write-Host ""
        Write-Host "Revisar logs del worker:" -ForegroundColor Yellow
        Write-Host "   docker-compose logs worker --tail 50" -ForegroundColor Gray
    }
} else {
    Write-Host "Test 4 omitido." -ForegroundColor Gray
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "TESTS COMPLETADOS" -ForegroundColor Yellow
Write-Host ("=" * 80) -ForegroundColor Cyan
