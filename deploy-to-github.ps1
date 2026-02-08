# Скрипт для загрузки проекта на GitHub
# Использование: .\deploy-to-github.ps1

Write-Host "`n=== Подготовка к загрузке на GitHub ===" -ForegroundColor Green

# Проверка наличия Git
try {
    $gitVersion = git --version 2>&1
    Write-Host "Git найден: $gitVersion" -ForegroundColor Cyan
} catch {
    Write-Host "ОШИБКА: Git не установлен!" -ForegroundColor Red
    Write-Host "Скачайте Git: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Проверка, инициализирован ли репозиторий
if (-not (Test-Path ".git")) {
    Write-Host "`nИнициализация git репозитория..." -ForegroundColor Yellow
    git init
    Write-Host "Репозиторий инициализирован" -ForegroundColor Green
} else {
    Write-Host "`nGit репозиторий уже инициализирован" -ForegroundColor Cyan
}

# Проверка статуса
Write-Host "`nПроверка изменений..." -ForegroundColor Yellow
$status = git status --porcelain

if ($status) {
    Write-Host "Найдены изменения:" -ForegroundColor Yellow
    git status --short
    
    Write-Host "`nДобавление файлов..." -ForegroundColor Yellow
    git add .
    
    $commitMessage = Read-Host "`nВведите сообщение коммита (или нажмите Enter для 'Initial commit')"
    if ([string]::IsNullOrWhiteSpace($commitMessage)) {
        $commitMessage = "Initial commit: White-Label Gateway MVP"
    }
    
    Write-Host "Создание коммита..." -ForegroundColor Yellow
    git commit -m $commitMessage
    Write-Host "Коммит создан" -ForegroundColor Green
} else {
    Write-Host "Нет изменений для коммита" -ForegroundColor Cyan
}

# Проверка remote
$remotes = git remote -v 2>&1
if ($remotes -match "origin") {
    Write-Host "`nRemote 'origin' уже настроен" -ForegroundColor Cyan
    Write-Host "Текущие remotes:" -ForegroundColor Yellow
    git remote -v
} else {
    Write-Host "`n=== Настройка GitHub ===" -ForegroundColor Green
    Write-Host "1. Создайте репозиторий на GitHub:" -ForegroundColor Yellow
    Write-Host "   - Перейдите на https://github.com/new" -ForegroundColor White
    Write-Host "   - Назовите репозиторий (например: white-label-gateway)" -ForegroundColor White
    Write-Host "   - НЕ создавайте README, .gitignore или лицензию" -ForegroundColor White
    Write-Host "   - Нажмите 'Create repository'" -ForegroundColor White
    
    $githubUrl = Read-Host "`n2. Введите URL вашего GitHub репозитория (например: https://github.com/username/white-label-gateway.git)"
    
    if ($githubUrl) {
        Write-Host "Добавление remote..." -ForegroundColor Yellow
        git remote add origin $githubUrl
        Write-Host "Remote добавлен" -ForegroundColor Green
        
        Write-Host "`nПереименование ветки в main..." -ForegroundColor Yellow
        git branch -M main
        
        Write-Host "`nЗагрузка на GitHub..." -ForegroundColor Yellow
        Write-Host "Введите ваши GitHub credentials при запросе" -ForegroundColor Cyan
        git push -u origin main
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n=== Успешно загружено на GitHub! ===" -ForegroundColor Green
            Write-Host "Репозиторий: $githubUrl" -ForegroundColor Cyan
        } else {
            Write-Host "`nОшибка при загрузке. Проверьте credentials и попробуйте снова:" -ForegroundColor Red
            Write-Host "  git push -u origin main" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`nПропущено добавление remote. Добавьте его вручную:" -ForegroundColor Yellow
        Write-Host "  git remote add origin https://github.com/username/repo-name.git" -ForegroundColor White
        Write-Host "  git branch -M main" -ForegroundColor White
        Write-Host "  git push -u origin main" -ForegroundColor White
    }
}

Write-Host "`n=== Готово! ===" -ForegroundColor Green
Write-Host "Следующие шаги:" -ForegroundColor Yellow
Write-Host "1. Если еще не создали репозиторий на GitHub - создайте его" -ForegroundColor White
Write-Host "2. Если не загрузили код - выполните: git push -u origin main" -ForegroundColor White
Write-Host "3. Для деплоя на Render см. DEPLOY.md" -ForegroundColor White
